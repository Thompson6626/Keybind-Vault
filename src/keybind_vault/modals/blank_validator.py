from textual.validation import Validator, ValidationResult


class Blank(Validator):
    def validate(self, value: str) -> ValidationResult:
        """Check a string is equal to its reverse."""
        if self.is_blank(value):
            return self.failure("Value can't be blank.")
        else:
            return self.success()

    @staticmethod
    def is_blank(value: str) -> bool:
        return not value.strip()
