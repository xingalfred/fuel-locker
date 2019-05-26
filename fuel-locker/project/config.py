class BaseConfig:
    """Base configuration"""

    SECRET_KEY = "my_precious"


class DevelopmentConfig(BaseConfig):
    """Development configuration"""


class TestingConfig(BaseConfig):
    """Testing configuration"""


class ProductionConfig(BaseConfig):
    """Production configuration"""
