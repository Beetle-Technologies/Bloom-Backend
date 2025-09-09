from typing import Optional

from sqlmodel import SQLModel, select

from ..exceptions import InvalidFieldError


class SelectionProvider:
    """Provider for constructing SELECT clauses with field selection"""

    def __init__(self, model: type[SQLModel]):
        self.model = model

    def build_select_query(self, select_fields: Optional[str] = None):
        """
        Build select query with optional field selection.

        Args:
            select_fields: Comma-separated string of fields to select or "*" for all fields

        Returns:
            SQLAlchemy select query

        Raises:
            InvalidFieldError: When one or more specified fields don't exist or aren't selectable
        """
        if not select_fields or select_fields.strip() == "*":
            # Select all fields (default behavior)
            return select(self.model)

        # Parse comma-separated field names
        field_names = [field.strip() for field in select_fields.split(",") if field.strip()]

        if not field_names:
            return select(self.model)

        # Validate fields against selectable fields
        invalid_fields, select_columns = self._validate_and_get_columns(field_names)

        if invalid_fields:
            valid_fields = self.get_selectable_fields()
            raise InvalidFieldError(invalid_fields=invalid_fields, valid_fields=valid_fields)

        if not select_columns:
            # If no valid columns found, default to selecting all
            return select(self.model)

        return select(*select_columns)

    def get_selected_fields(self, select_fields: Optional[str] = None) -> list[str]:
        """
        Get list of field names that will be selected.

        Args:
            select_fields: Comma-separated string of fields to select or "*" for all fields

        Returns:
            List of field names that will be selected
        """
        if not select_fields or select_fields.strip() == "*":
            # Return all selectable field names
            return self.get_selectable_fields()

        # Parse comma-separated field names
        field_names = [field.strip() for field in select_fields.split(",") if field.strip()]

        # Filter to only include valid selectable fields
        selectable_fields = self.get_selectable_fields()
        valid_fields = [
            field_name
            for field_name in field_names
            if field_name in selectable_fields and hasattr(self.model, field_name)
        ]

        return valid_fields if valid_fields else self.get_selectable_fields()

    def validate_fields(self, select_fields: Optional[str] = None) -> None:
        """
        Validate that all specified fields exist on the model and are selectable.

        Args:
            select_fields: Comma-separated string of fields to select

        Raises:
            InvalidFieldError: When one or more specified fields don't exist or aren't selectable
        """
        if not select_fields or select_fields.strip() == "*":
            return

        field_names = [field.strip() for field in select_fields.split(",") if field.strip()]

        invalid_fields, _ = self._validate_and_get_columns(field_names)

        if invalid_fields:
            valid_fields = self.get_selectable_fields()
            raise InvalidFieldError(invalid_fields=invalid_fields, valid_fields=valid_fields)

    def get_selectable_fields(self) -> list[str]:
        """
        Get list of fields that are selectable for this model.

        Returns:
            List of selectable field names
        """
        # Check if model has a SELECTABLE_FIELDS constant
        if hasattr(self.model, "SELECTABLE_FIELDS"):
            return list(getattr(self.model, "SELECTABLE_FIELDS"))

        # Fallback to all model fields if no SELECTABLE_FIELDS defined
        return [name for name, _ in self.model.__fields__.items()]

    def _validate_and_get_columns(self, field_names: list[str]) -> tuple[list[str], list]:
        """
        Validate field names and return invalid fields and valid columns.

        Args:
            field_names: List of field names to validate

        Returns:
            Tuple of (invalid_fields, select_columns)
        """
        invalid_fields = []
        select_columns = []
        selectable_fields = self.get_selectable_fields()

        for field_name in field_names:
            # Handle nested field paths (e.g., "account.display_name")
            if "." in field_name:
                # For now, we'll skip relationship fields in select
                invalid_fields.append(field_name)
                continue

            # Check if field exists on model and is selectable
            if hasattr(self.model, field_name) and field_name in selectable_fields:
                select_columns.append(getattr(self.model, field_name))
            else:
                invalid_fields.append(field_name)

        return invalid_fields, select_columns
