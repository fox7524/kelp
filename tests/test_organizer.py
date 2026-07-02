import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

from src.organizer.utils import (
    normalize_text,
    match_activity_keywords,
    get_safe_destination,
    get_file_date_folder
)
from src.organizer.duplicate_finder import scan_for_duplicates, resolve_duplicates_interactive
from src.organizer.hierarchy_rearranger import rearrange_hierarchy

def test_normalize_text():
    assert normalize_text("Alper Gezeravcı Video") == "alper gezeravci video"
    assert normalize_text("YİTİK ZAMANIN İZİNDE") == "yitik zamanin izinde"
    assert normalize_text("Türkçe Şarkı Örneği ÜÇ") == "turkce sarki ornegi uc"

def test_match_activity_keywords():
    keywords = ["alper gezeravcı", "yitik zamanın izinde"]
    
    assert match_activity_keywords("alper_gezeravci_video.mp4", keywords) == "alper gezeravcı"
    assert match_activity_keywords("Yitik Zamanın Izinde Kapak.png", keywords) == "yitik zamanın izinde"
    assert match_activity_keywords("yitik_zamanin_izinde.jpg", keywords) == "yitik zamanın izinde"
    assert match_activity_keywords("random_photo.jpg", keywords) is None

def test_get_safe_destination(tmp_path):
    dest = tmp_path / "test_file.txt"
    # No file exists yet
    assert get_safe_destination(dest) == dest
    
    # Create file
    dest.touch()
    safe_dest1 = get_safe_destination(dest)
    assert safe_dest1 == tmp_path / "test_file_1.txt"
    
    # Create safe_dest1
    safe_dest1.touch()
    safe_dest2 = get_safe_destination(dest)
    assert safe_dest2 == tmp_path / "test_file_2.txt"

def test_get_file_date_folder(tmp_path):
    f = tmp_path / "test.txt"
    f.touch()
    folder = get_file_date_folder(f)
    assert len(folder) == 7  # YYYY-MM
    assert folder[4] == '-'

def test_scan_for_duplicates(tmp_path):
    # Setup files:
    # A1, A2, A3 have content "A"
    # B1, B2 have content "B"
    # C1 has content "C" (unique)
    
    d1 = tmp_path / "dir1"
    d2 = tmp_path / "dir2"
    d1.mkdir()
    d2.mkdir()
    
    (d1 / "a1.txt").write_text("content A")
    (d2 / "a2.txt").write_text("content A")
    (tmp_path / "a3.txt").write_text("content A")
    
    (d1 / "b1.txt").write_text("content B")
    (d2 / "b2.txt").write_text("content B")
    
    (d1 / "c1.txt").write_text("content C")
    
    # Find duplicates
    dups = scan_for_duplicates(tmp_path)
    
    # Should find two groups
    assert len(dups) == 2
    
    # Verify group contents (lengths)
    group_sizes = [len(g) for g in dups]
    assert sorted(group_sizes) == [2, 3]

def test_resolve_duplicates_interactive(tmp_path):
    d1 = tmp_path / "dir1"
    d1.mkdir()
    
    file1 = d1 / "a1.txt"
    file2 = d1 / "a2.txt"
    
    file1.write_text("same content")
    file2.write_text("same content")
    
    duplicates = [[file1, file2]]
    
    # Mock user input to choose file index 1 (keep file1, backup file2)
    with patch("src.organizer.duplicate_finder.Prompt.ask", return_value="1"):
        resolve_duplicates_interactive(tmp_path, duplicates, dry_run=False)
        
    # Check that file1 still exists
    assert file1.exists()
    
    # Check that file2 is moved to the backup directory
    backup_dir = tmp_path / "_duplicates_backup"
    assert backup_dir.exists()
    
    backup_file2 = backup_dir / "dir1" / "a2.txt"
    assert backup_file2.exists()
    assert backup_file2.read_text() == "same content"
    assert not file2.exists()

def test_rearrange_hierarchy(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    
    # Create test files
    f1 = source / "alper_gezeravci_video.mp4"
    f2 = source / "yitik_zamanin_izinde_kapak.png"
    f3 = source / "regular_photo.jpg"
    
    f1.write_text("video contents")
    f2.write_text("cover contents")
    f3.write_text("photo contents")
    
    keywords = ["alper gezeravcı", "yitik zamanın izinde"]
    
    # Run rearranger (copy mode)
    stats = rearrange_hierarchy(source, dest, keywords, action="copy", dry_run=False)
    
    assert stats["copied"] == 3
    assert stats["failed"] == 0
    
    # Verify dest folders
    alper_dir = dest / "alper gezeravcı"
    yitik_dir = dest / "yitik zamanın izinde"
    
    assert alper_dir.exists()
    assert (alper_dir / "alper_gezeravci_video.mp4").exists()
    
    assert yitik_dir.exists()
    assert (yitik_dir / "yitik_zamanin_izinde_kapak.png").exists()
    
    # The regular_photo.jpg should be in date folder (YYYY-MM)
    date_folder_name = get_file_date_folder(f3)
    date_dir = dest / date_folder_name
    assert date_dir.exists()
    assert (date_dir / "regular_photo.jpg").exists()
    
    # Check that source files still exist (because of copy action)
    assert f1.exists()
    assert f2.exists()
    assert f3.exists()

def test_rearrange_hierarchy_move_mode(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    
    f1 = source / "alper_gezeravci_video.mp4"
    f1.write_text("video contents")
    
    keywords = ["alper gezeravcı"]
    
    # Run rearranger (move mode)
    stats = rearrange_hierarchy(source, dest, keywords, action="move", dry_run=False)
    
    assert stats["moved"] == 1
    assert not f1.exists()  # should have been moved
    assert (dest / "alper gezeravcı" / "alper_gezeravci_video.mp4").exists()
