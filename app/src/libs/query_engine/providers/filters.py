from typing import Any

from sqlmodel import SQLModel, and_, col, func, not_, or_


class FiltersProvider:
    """Builder for constructing complex filter conditions"""

    def __init__(self, model: type[SQLModel]):
        self.model = model

    def build_filter_conditions(self, filters: dict[str, Any]):
        """
        Build complex filter conditions with support for logical operators.

        Supports patterns like:
        - "field__operator": value (e.g., "name__ilike": "john")
        - "field__or__field2__operator": value (e.g., "account.first_name__or__account.email__ilike": "john")
        - "field__and__field2__operator": value (e.g., "account.first_name__and__account.email__eq": "john")
        - "field__not__operator": value (e.g., "account.display_name__not__eq": "admin")

        Args:
            filters: Dictionary of filter conditions

        Returns:
            SQLAlchemy filter condition or None
        """
        if not filters:
            return None

        conditions = []

        for filter_key, value in filters.items():
            condition = self._parse_filter_condition(filter_key, value)
            if condition is not None:
                conditions.append(condition)

        if not conditions:
            return None

        # Combine all conditions with AND by default
        return and_(*conditions) if len(conditions) > 1 else conditions[0]

    def _parse_filter_condition(self, filter_key: str, value: Any):
        """Parse a single filter condition"""
        if "__" not in filter_key:
            # Simple equality filter
            return self._build_simple_condition(filter_key, "eq", value)

        # Handle complex filter patterns like "account.first_name__or__account.email__ilike"
        parts = filter_key.split("__")

        # Find logical operators and operator
        logical_ops = []
        field_parts = []
        operator = None

        i = 0
        current_field = ""

        while i < len(parts):
            part = parts[i]

            if part in ["or", "and", "not"]:
                if current_field:
                    field_parts.append(current_field)
                    current_field = ""
                logical_ops.append(part)
            elif part in [
                "eq",
                "ne",
                "lt",
                "le",
                "gt",
                "ge",
                "like",
                "ilike",
                "in",
                "notin",
                "is_null",
                "is_not_null",
            ]:
                operator = part
                if current_field:
                    field_parts.append(current_field)
                break
            else:
                current_field = current_field + "." + part if current_field else part

            i += 1

        # Add any remaining field
        if current_field and operator:
            field_parts.append(current_field)

        # If we have logical operators and multiple fields, handle them
        if logical_ops and len(field_parts) > 1:
            return self._build_logical_condition(field_parts, logical_ops, operator, value)

        # Standard field__operator pattern
        if len(parts) >= 2:
            field_path = "__".join(parts[:-1])
            operator = parts[-1]
            return self._build_simple_condition(field_path, operator, value)

        return None

    def _build_logical_condition(
        self,
        field_parts: list[str],
        logical_operators: list[str],
        operator: str | None,
        value: Any,
    ):
        """Build logical condition (OR, AND, NOT)"""
        conditions = []

        for field_path in field_parts:
            condition = self._build_simple_condition(field_path, operator, value)
            if condition is not None:
                conditions.append(condition)

        if not conditions:
            return None

        # Apply logical operators
        if "or" in logical_operators:
            result = or_(*conditions)
        elif "and" in logical_operators:
            result = and_(*conditions)
        else:
            result = and_(*conditions)

        if "not" in logical_operators:
            result = not_(result)

        return result

    def _build_simple_condition(self, field_path: str, operator: str | None, value: Any):
        """Build a simple condition for a field"""
        if operator is None:
            return None

        try:
            # Handle nested field paths (e.g., "account.display_name")
            if "." in field_path:
                parts = field_path.split(".")
                if len(parts) == 2 and hasattr(self.model, parts[0]):
                    # Get the relationship
                    relationship_attr = getattr(self.model, parts[0])

                    # Get the target model class from the relationship
                    if hasattr(relationship_attr.property, "mapper"):
                        target_model = relationship_attr.property.mapper.class_
                        if hasattr(target_model, parts[1]):
                            field_attr = getattr(target_model, parts[1])
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            else:
                # Simple field
                if not hasattr(self.model, field_path):
                    return None
                field_attr = getattr(self.model, field_path)

            # Apply operator
            return self._apply_operator(field_attr, operator, value)

        except (AttributeError, TypeError):
            return None

    def _apply_operator(self, field_attr, operator: str, value: Any):
        """Apply the specified operator to the field"""
        field_col = col(field_attr)

        if operator == "eq":
            return field_col == value
        elif operator == "ne":
            return field_col != value
        elif operator == "gt":
            return field_col > value
        elif operator == "gte":
            return field_col >= value
        elif operator == "lt":
            return field_col < value
        elif operator == "lte":
            return field_col <= value
        elif operator == "like":
            return field_col.like(f"%{value}%")
        elif operator == "ilike":
            return field_col.ilike(f"%{value}%")
        elif operator == "startswith":
            return field_col.like(f"{value}%")
        elif operator == "endswith":
            return field_col.like(f"%{value}")
        elif operator == "contains":
            return field_col.contains(value)
        elif operator == "in":
            if isinstance(value, (list, tuple)):
                return field_col.in_(value)
            return field_col.in_([value])
        elif operator == "not_in":
            if isinstance(value, (list, tuple)):
                return ~field_col.in_(value)
            return ~field_col.in_([value])
        elif operator == "is_null":
            return field_col.is_(None)
        elif operator == "is_not_null":
            return field_col.is_not(None)
        elif operator == "between":
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return field_col.between(value[0], value[1])
            return None
        elif operator == "search":
            return field_col.op("@@")(func.to_tsquery("english", value))
        else:
            return None

    def get_required_joins(self, filters: dict[str, Any]) -> list[str]:
        """
        Determine which relationships need to be joined for the given filters.

        Returns:
            List of relationship names that need to be joined
        """
        joins = set()

        for filter_key in filters.keys():
            # Parse the filter key to find relationship references
            if "." in filter_key:
                # Handle patterns like "account.first_name__or__account.email__ilike"
                parts = filter_key.split("__")

                for part in parts:
                    if "." in part:
                        # This part contains a relationship reference
                        field_parts = part.split(".")
                        if len(field_parts) >= 2 and hasattr(self.model, field_parts[0]):
                            joins.add(field_parts[0])

        return list(joins)
