from sqlmodel import SQLModel, and_, col, or_

from ..schemas import KeysetCursor, KeysetField, SortDirection


class KeysetProvider:
    """Builder for constructing keyset pagination queries"""

    def __init__(self, model: type[SQLModel]):
        self.model = model

    def build_where_clause(self, cursor: KeysetCursor, reverse: bool = False):
        """
        Build WHERE clause for keyset pagination

        Args:
            cursor: The keyset cursor
            reverse: If True, reverse the comparison for backward pagination
        """
        if not cursor.fields:
            return None

        # For compound cursors, we need to build a proper comparison
        # For (a, b) > (x, y): (a > x) OR (a = x AND b > y)
        conditions = []

        for i in range(len(cursor.fields)):
            # Build condition for this level
            level_conditions = []

            # Add equality conditions for all previous fields
            for j in range(i):
                field = cursor.fields[j]
                model_attr = getattr(self.model, field.name)
                level_conditions.append(col(model_attr) == field.value)

            # Add comparison for current field
            current_field = cursor.fields[i]
            model_attr = getattr(self.model, current_field.name)

            # Determine comparison operator based on direction and reverse flag
            if current_field.direction == SortDirection.ASC:
                if reverse:
                    comparison = col(model_attr) < current_field.value
                else:
                    comparison = col(model_attr) > current_field.value
            else:  # DESC
                if reverse:
                    comparison = col(model_attr) > current_field.value
                else:
                    comparison = col(model_attr) < current_field.value

            level_conditions.append(comparison)

            # Combine with AND
            if level_conditions:
                conditions.append(and_(*level_conditions))

        # Combine all conditions with OR
        return or_(*conditions) if conditions else None

    def build_order_clause(self, sort_fields: list[tuple[str, SortDirection]], reverse: bool = False):
        """Build ORDER BY clause"""
        order_clauses = []

        for field_name, direction in sort_fields:
            model_attr = getattr(self.model, field_name)

            # Reverse direction if this is a reverse query
            if reverse:
                actual_direction = SortDirection.DESC if direction == SortDirection.ASC else SortDirection.ASC
            else:
                actual_direction = direction

            if actual_direction == SortDirection.ASC:
                order_clauses.append(col(model_attr).asc())
            else:
                order_clauses.append(col(model_attr).desc())

        return order_clauses

    def create_cursor_from_row(self, row: SQLModel, sort_fields: list[tuple[str, SortDirection]]) -> KeysetCursor:
        """Create a cursor from a database row"""
        fields = []

        for field_name, direction in sort_fields:
            value = getattr(row, field_name)
            fields.append(KeysetField(name=field_name, value=value, direction=direction))

        return KeysetCursor(fields=fields, is_previous=False)

    def ensure_unique_sort(self, sort_fields: list[tuple[str, SortDirection]]) -> list[tuple[str, SortDirection]]:
        """
        Ensure the sort includes a unique field (typically 'id') for stable pagination.
        This prevents issues with duplicate values in sort fields.
        """
        field_names = [name for name, _ in sort_fields]

        # Check if we already have a unique field
        unique_fields = ["id"]  # Add other unique fields as needed
        has_unique = any(field in field_names for field in unique_fields)

        if not has_unique:
            # Add 'id' as the last sort field with the same direction as the first field
            primary_direction = sort_fields[0][1] if sort_fields else SortDirection.ASC
            if hasattr(self.model, "id"):
                sort_fields.append(("id", primary_direction))

        return sort_fields
