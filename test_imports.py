
import sys
print("Python version:", sys.version)

try:
    from pydantic_settings import BaseSettings
    print("BaseSettings imported successfully")
    
    # Test if we can create a minimal config class  
    from pydantic import BaseModel
    
    class TestConfig(BaseSettings):
        test_field: str = "default"
        
        class Config(BaseSettings.Config):
            case_sensitive = False
            
    print("Minimal config works correctly") 
    
except Exception as e:
    print(f"Error with imports: {e}")
