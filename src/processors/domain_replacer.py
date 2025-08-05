"""
Domain Replacement Processor
Handles the core logic for replacing email domains in CSV files
"""

import os
import re
from datetime import datetime
from typing import Any, Dict

import pandas as pd


class DomainReplacer:
    """Handles email domain replacement in CSV files"""

    def __init__(self, max_rows_limit: int = 100000):
        """
        Initialize the domain replacer

        Args:
            max_rows_limit: Maximum number of rows to process
        """
        self.max_rows_limit = max_rows_limit

    def replace_domains(
        self, filepath: str, old_domain: str, new_domain: str, output_dir: str
    ) -> Dict[str, Any]:
        """
        Process CSV file and replace email domains

        Args:
            filepath: Path to the input CSV file
            old_domain: Domain to be replaced
            new_domain: New domain to replace with
            output_dir: Directory to save the processed file

        Returns:
            Dictionary containing processing results
        """
        try:
            # Read CSV file
            df = pd.read_csv(filepath)

            if df.empty:
                return {"success": False, "error": "CSV file is empty"}

            if len(df) > self.max_rows_limit:
                return {
                    "success": False,
                    "error": (
                        f"File exceeds maximum row limit of {self.max_rows_limit:,}"
                    ),
                }

            changes_made = 0
            email_pattern = rf"([a-zA-Z0-9._%+-]+)@{re.escape(old_domain)}"
            replacement = rf"\1@{new_domain}"

            # Process each column
            for col in df.columns:
                if df[col].dtype == "object":  # Only process string columns
                    original_values = df[col].astype(str)
                    updated_values = original_values.str.replace(
                        email_pattern, replacement, regex=True, case=False
                    )

                    # Count changes in this column
                    changes_in_col = (original_values != updated_values).sum()
                    changes_made += changes_in_col

                    # Update the column
                    df[col] = updated_values

            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"mailmorph_output_{timestamp}.csv"
            output_path = os.path.join(output_dir, output_filename)

            # Save processed file
            df.to_csv(output_path, index=False)

            return {
                "success": True,
                "output_file": output_filename,
                "changes_made": changes_made,
                "total_rows": len(df),
                "old_domain": old_domain,
                "new_domain": new_domain,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            return {"success": False, "error": "Unable to process file. Please ensure it's a valid CSV with proper formatting and try again."}

    def preview_changes(
        self, filepath: str, old_domain: str, new_domain: str, sample_size: int = 10
    ) -> Dict[str, Any]:
        """
        Preview changes that would be made without actually processing the file

        Args:
            filepath: Path to the input CSV file
            old_domain: Domain to be replaced
            new_domain: New domain to replace with
            sample_size: Number of sample rows to return

        Returns:
            Dictionary containing preview results
        """
        try:
            df = pd.read_csv(filepath)

            if df.empty:
                return {"success": False, "error": "CSV file is empty"}

            email_pattern = rf"([a-zA-Z0-9._%+-]+)@{re.escape(old_domain)}"
            replacement = rf"\1@{new_domain}"

            preview_data = []
            total_matches = 0

            # Process each column to find matches
            for col in df.columns:
                if df[col].dtype == "object":
                    original_values = df[col].astype(str)
                    matches = original_values.str.contains(
                        email_pattern, regex=True, case=False
                    )

                    if matches.any():
                        total_matches += matches.sum()

                        # Get sample of matching rows
                        matching_rows = df[matches].head(sample_size)
                        for idx, row in matching_rows.iterrows():
                            original = str(row[col])
                            updated = re.sub(
                                email_pattern,
                                replacement,
                                original,
                                flags=re.IGNORECASE,
                            )

                            preview_data.append(
                                {
                                    "column": col,
                                    "row": int(idx),
                                    "original": original,
                                    "updated": updated,
                                }
                            )

            return {
                "success": True,
                "total_matches": int(total_matches),
                "total_rows": len(df),
                "preview_data": preview_data[:sample_size],
                "old_domain": old_domain,
                "new_domain": new_domain,
            }

        except Exception as e:
            return {"success": False, "error": "Unable to preview file changes. Please verify the file format and try again."}
