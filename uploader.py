#!/usr/bin/env python3
"""Upload / sync designs to Printify or Etsy.

This module is a lightweight pipeline entrypoint for the Etsy upload queue.
"""

from __future__ import annotations

from ai_factory.etsy.etsy_upload import process_etsy_upload_queue

if __name__ == "__main__":
    result = process_etsy_upload_queue(dry_run=True)
    print("Etsy upload queue processed in dry run mode.")
    print(result)
