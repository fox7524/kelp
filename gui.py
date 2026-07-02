import sys
import os
import re
import shutil
import threading
from pathlib import Path
from collections import defaultdict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QRadioButton,
    QButtonGroup, QCheckBox, QProgressBar, QPlainTextEdit, QMessageBox,
    QDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon

# Ensure parent directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.organizer.duplicate_finder import scan_for_duplicates, get_human_readable_size
from src.organizer.hierarchy_rearranger import rearrange_hierarchy
from src.organizer.duplicate_dialog import DuplicateDialog
from src.organizer.utils import get_safe_destination

class LogCaptureStream:
    """Redirects stdout to a Qt signal, stripping ANSI color escape codes."""
    def __init__(self, signal: pyqtSignal):
        self.signal = signal
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def write(self, text):
        clean_text = self.ansi_escape.sub('', text)
        if clean_text:
            self.signal.emit(clean_text)

    def flush(self):
        pass

class OrganizerWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    show_duplicates_signal = pyqtSignal(list, Path)
    finished_signal = pyqtSignal(dict)

    def __init__(self, source_dir: Path, dest_dir: Path, keywords: list[str], action: str, dry_run: bool):
        super().__init__()
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.keywords = keywords
        self.action = action
        self.dry_run = dry_run
        
        # Synchronization for duplicate dialog response
        self.duplicate_event = threading.Event()
        self.duplicate_selections = None  # Populated by main GUI thread
        self.aborted = False

    def run(self):
        # Redirect stdout to capture prints from backend logic
        sys.stdout = LogCaptureStream(self.log_signal)
        sys.stderr = LogCaptureStream(self.log_signal)

        try:
            self.status_signal.emit("Scanning for duplicate files...")
            self.progress_signal.emit(10)
            
            # Step 1: Scan for duplicates
            print(f"Scanning directory: {self.source_dir} for identical files...")
            duplicates = scan_for_duplicates(self.source_dir)
            
            self.progress_signal.emit(30)
            
            # Step 2: Handle Duplicates if found
            backup_dir = self.source_dir / "_duplicates_backup"
            total_freed_space = 0
            moved_duplicates_count = 0
            
            if duplicates:
                print(f"Detected {len(duplicates)} groups of duplicate files.")
                self.status_signal.emit("Waiting for duplicate selections...")
                
                # Signal the GUI thread to show the Duplicate Selection Dialog
                self.duplicate_event.clear()
                self.show_duplicates_signal.emit(duplicates, self.source_dir)
                
                # Block here until the user accepts/rejects the dialog
                self.duplicate_event.wait()
                
                if self.aborted or self.duplicate_selections is None:
                    print("Duplicate resolution cancelled. Aborting organization pipeline.")
                    self.status_signal.emit("Aborted.")
                    self.finished_signal.emit({"aborted": True})
                    return
                
                # User choices processed
                self.status_signal.emit("Moving duplicates to backup folder...")
                print("\nProcessing duplicates:")
                
                if self.dry_run:
                    print("[Dry-run] Would move duplicates to backup folder.")
                    # Calculate estimated savings
                    for g_idx, keep_path in self.duplicate_selections.items():
                        if keep_path:
                            group = duplicates[g_idx]
                            discard_paths = [p for p in group if p != keep_path]
                            for dp in discard_paths:
                                try:
                                    total_freed_space += dp.stat().st_size
                                    moved_duplicates_count += 1
                                except Exception:
                                    pass
                else:
                    for g_idx, keep_path in self.duplicate_selections.items():
                        if not keep_path:
                            print(f"Group #{g_idx+1}: Keeping all files.")
                            continue
                            
                        group = duplicates[g_idx]
                        discard_paths = [p for p in group if p != keep_path]
                        
                        print(f"Group #{g_idx+1}: Keeping '{keep_path.name}'. Moving duplicates to backup:")
                        for discard_path in discard_paths:
                            try:
                                file_size = discard_path.stat().st_size
                                try:
                                    rel_path = discard_path.relative_to(self.source_dir)
                                except ValueError:
                                    rel_path = discard_path.name
                                    
                                dest_path = backup_dir / rel_path
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Safe renaming inside backup folder
                                dest_path = get_safe_destination(dest_path)
                                
                                shutil.move(str(discard_path), str(dest_path))
                                total_freed_space += file_size
                                moved_duplicates_count += 1
                                print(f"  • {discard_path.name} -> backup/{rel_path}")
                            except Exception as e:
                                print(f"  • Error backing up {discard_path.name}: {e}")
            else:
                print("No duplicate files found.")
                
            self.progress_signal.emit(50)
            
            # Step 3: Rearrange Hierarchy
            self.status_signal.emit("Rearranging folder structure...")
            print("\nStarting folder rearrangement...")
            
            stats = rearrange_hierarchy(
                source_dir=self.source_dir,
                dest_dir=self.dest_dir,
                keywords=self.keywords,
                action=self.action,
                dry_run=self.dry_run
            )
            
            self.progress_signal.emit(100)
            self.status_signal.emit("Finished!")
            
            # Combine duplicate summary and rearrangement summary
            final_summary = {
                "aborted": False,
                "freed_space_str": get_human_readable_size(total_freed_space),
                "moved_duplicates": moved_duplicates_count,
                "rearranged_total": stats.get("total", 0),
                "rearranged_success": stats.get("copied", 0) if self.action == "copy" else stats.get("moved", 0),
                "rearranged_collisions": stats.get("collisions", 0),
                "rearranged_failed": stats.get("failed", 0),
                "action": self.action
            }
            
            self.finished_signal.emit(final_summary)

        except Exception as e:
            print(f"\nCritical Exception occurred during pipeline: {e}")
            self.status_signal.emit("Failed.")
            self.finished_signal.emit({"failed": True, "error": str(e)})
        finally:
            # Restore original streams
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.apply_stylesheet()
        
    def init_ui(self):
        self.setWindowTitle("Kelp - File Organizer & Duplicate Finder")
        self.resize(800, 650)
        self.setMinimumSize(700, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Application Header Title
        title_label = QLabel("Kelp File Organizer")
        title_label.setObjectName("appTitle")
        main_layout.addWidget(title_label)
        
        # Subtitle instructions
        subtitle_label = QLabel("Organize files recursively using dates or custom keywords, and safely backup duplicate files.")
        subtitle_label.setObjectName("appSubtitle")
        main_layout.addWidget(subtitle_label)
        
        # 1. Inputs Section
        inputs_layout = QVBoxLayout()
        inputs_layout.setSpacing(12)
        
        # Source Directory (Mixed folder)
        src_label = QLabel("Source Folder (Mixed Files):")
        inputs_layout.addWidget(src_label)
        
        src_row = QHBoxLayout()
        self.txt_source = QLineEdit()
        self.txt_source.setPlaceholderText("Select the folder from your external HDD containing mixed files...")
        self.btn_browse_src = QPushButton("Browse...")
        self.btn_browse_src.clicked.connect(self.browse_source)
        src_row.addWidget(self.txt_source)
        src_row.addWidget(self.btn_browse_src)
        inputs_layout.addLayout(src_row)
        
        # Destination Directory (Organized folder)
        dest_label = QLabel("Destination Folder (Final Destination):")
        inputs_layout.addWidget(dest_label)
        
        dest_row = QHBoxLayout()
        self.txt_dest = QLineEdit()
        self.txt_dest.setPlaceholderText("Select the destination folder where files will be organized...")
        self.btn_browse_dest = QPushButton("Browse...")
        self.btn_browse_dest.clicked.connect(self.browse_dest)
        dest_row.addWidget(self.txt_dest)
        dest_row.addWidget(self.btn_browse_dest)
        inputs_layout.addLayout(dest_row)
        
        # Keywords input
        kw_label = QLabel("Activity Keywords (Comma-separated list to group specific topics):")
        inputs_layout.addWidget(kw_label)
        self.txt_keywords = QLineEdit()
        self.txt_keywords.setPlaceholderText("e.g. alper gezeravcı, yitik zamanın izinde, cover page")
        inputs_layout.addWidget(self.txt_keywords)
        
        main_layout.addLayout(inputs_layout)
        
        # 2. Settings Row (Action Mode, Dry-Run)
        settings_row = QHBoxLayout()
        settings_row.setSpacing(25)
        
        # Action selector group
        action_label = QLabel("File Action:")
        settings_row.addWidget(action_label)
        
        self.btn_group_action = QButtonGroup(self)
        self.rad_copy = QRadioButton("Copy (Recommended/Safe)")
        self.rad_copy.setChecked(True)
        self.rad_move = QRadioButton("Move (Rearrange In-Place)")
        self.btn_group_action.addButton(self.rad_copy, 1)
        self.btn_group_action.addButton(self.rad_move, 2)
        settings_row.addWidget(self.rad_copy)
        settings_row.addWidget(self.rad_move)
        
        # Dry-run checkbox
        self.chk_dry_run = QCheckBox("Dry-run (simulation only)")
        settings_row.addWidget(self.chk_dry_run)
        
        settings_row.addStretch()
        main_layout.addLayout(settings_row)
        
        # 3. Action execution panel
        self.btn_start = QPushButton("Start Organization Process")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.clicked.connect(self.start_pipeline)
        main_layout.addWidget(self.btn_start)
        
        # 4. Progress and Console
        progress_layout = QHBoxLayout()
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setObjectName("lblStatus")
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        progress_layout.addWidget(self.lbl_status)
        progress_layout.addWidget(self.pbar)
        main_layout.addLayout(progress_layout)
        
        # Log Box Terminal
        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setPlaceholderText("Pipeline execution logs will appear here...")
        main_layout.addWidget(self.txt_logs)
        
        self.worker = None

    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if folder:
            self.txt_source.setText(folder)

    def browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if folder:
            self.txt_dest.setText(folder)

    def start_pipeline(self):
        src_path = self.txt_source.text().strip()
        dest_path = self.txt_dest.text().strip()
        
        if not src_path or not os.path.isdir(src_path):
            QMessageBox.warning(self, "Input Error", "Please select a valid Source Folder.")
            return
            
        if not dest_path:
            QMessageBox.warning(self, "Input Error", "Please select a valid Destination Folder.")
            return
            
        if src_path == dest_path:
            QMessageBox.warning(self, "Input Error", "Source and Destination folders cannot be identical.")
            return
            
        # Parse keywords
        kw_input = self.txt_keywords.text().strip()
        keywords = [kw.strip() for kw in kw_input.split(",") if kw.strip()]
        
        action = "copy" if self.rad_copy.isChecked() else "move"
        dry_run = self.chk_dry_run.isChecked()
        
        # Prepare UI
        self.txt_logs.clear()
        self.pbar.setValue(0)
        self.btn_start.setEnabled(False)
        self.btn_browse_src.setEnabled(False)
        self.btn_browse_dest.setEnabled(False)
        
        # Create and launch worker thread
        self.worker = OrganizerWorker(
            source_dir=Path(src_path),
            dest_dir=Path(dest_path),
            keywords=keywords,
            action=action,
            dry_run=dry_run
        )
        
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.status_signal.connect(self.lbl_status.setText)
        self.worker.show_duplicates_signal.connect(self.handle_duplicates)
        self.worker.finished_signal.connect(self.on_pipeline_finished)
        
        self.worker.start()

    def append_log(self, text):
        self.txt_logs.appendPlainText(text)
        # Auto-scroll to bottom
        self.txt_logs.ensureCursorVisible()

    def handle_duplicates(self, duplicates, scan_root):
        """Called when worker finds duplicates. Opens dialog in GUI thread."""
        dialog = DuplicateDialog(duplicates, scan_root, self)
        if dialog.exec_() == QDialog.Accepted:
            self.worker.duplicate_selections = dialog.get_selections()
        else:
            self.worker.aborted = True
            
        # Notify worker thread to resume
        self.worker.duplicate_event.set()

    def on_pipeline_finished(self, summary):
        self.btn_start.setEnabled(True)
        self.btn_browse_src.setEnabled(True)
        self.btn_browse_dest.setEnabled(True)
        
        if summary.get("aborted"):
            QMessageBox.information(self, "Cancelled", "The organization process was cancelled.")
            self.lbl_status.setText("Aborted.")
            return
            
        if summary.get("failed"):
            QMessageBox.critical(self, "Error", f"A critical error occurred:\n{summary.get('error')}")
            self.lbl_status.setText("Failed.")
            return
            
        # Build success message dialog
        mode_noun = "Copied" if summary["action"] == "copy" else "Moved"
        msg = (
            f"Organization pipeline finished successfully!\n\n"
            f"• Duplicate files backed up: {summary['moved_duplicates']} files\n"
            f"• Freed duplicate space: {summary['freed_space_str']}\n"
            f"• Files {mode_noun.lower()}: {summary['rearranged_success']} of {summary['rearranged_total']} files\n"
            f"• Name collisions resolved: {summary['rearranged_collisions']} files\n"
            f"• Failures: {summary['rearranged_failed']} files"
        )
        
        QMessageBox.information(self, "Success", msg)
        self.lbl_status.setText("Ready")
        self.pbar.setValue(100)

    def apply_stylesheet(self):
        # Premium Dark Palette (Catppuccin Mocha style)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
                font-weight: 500;
            }
            QLabel#appTitle {
                font-size: 24px;
                font-weight: bold;
                color: #89b4fa;
            }
            QLabel#appSubtitle {
                color: #a6adc8;
                font-size: 13px;
                margin-bottom: 5px;
            }
            QLabel#lblStatus {
                color: #fab387;
                font-weight: bold;
                min-width: 150px;
            }
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                color: #cdd6f4;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            QPushButton#btnStart {
                background-color: #89b4fa;
                color: #11111b;
                padding: 12px 20px;
                font-size: 15px;
                border-radius: 8px;
            }
            QPushButton#btnStart:hover {
                background-color: #b4befe;
            }
            QPushButton#btnStart:pressed {
                background-color: #74c7ec;
            }
            QPushButton#btnStart:disabled {
                background-color: #585b70;
                color: #a6adc8;
            }
            QRadioButton, QCheckBox {
                color: #cdd6f4;
                spacing: 8px;
                font-size: 13px;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator::unchecked, QCheckBox::indicator::unchecked {
                border: 2px solid #585b70;
                border-radius: 8px;
                background-color: transparent;
            }
            QCheckBox::indicator::unchecked {
                border-radius: 4px;
            }
            QRadioButton::indicator::checked {
                border: 2px solid #89b4fa;
                border-radius: 8px;
                background-color: #89b4fa;
            }
            QCheckBox::indicator::checked {
                border: 2px solid #89b4fa;
                border-radius: 4px;
                background-color: #89b4fa;
            }
            QProgressBar {
                background-color: #313244;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: #cdd6f4;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 8px;
            }
            QPlainTextEdit {
                background-color: #11111b;
                border: 1px solid #313244;
                border-radius: 8px;
                color: #a6e3a1;
                font-family: 'Courier New', Courier, monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
