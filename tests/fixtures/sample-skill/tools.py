class SkillRuntime:
    def __init__(self, greeting: str = "Hello"):
        self.greeting = greeting

    def greet_user(self, name: str) -> str:
        """Greet a user by name and return a greeting string."""
        return f"{self.greeting}, {name}!"

    def get_greeting(self) -> str:
        """Return the current greeting word."""
        return self.greeting

    def get_tools(self) -> list:
        return [self.greet_user, self.get_greeting]
