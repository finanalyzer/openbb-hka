from functools import wraps
import json
import os
import asyncio
from pathlib import Path

# Initialize empty dictionaries for widgets and templates
WIDGETS = {}
TEMPLATES = {}

def register_widget(widget_config):
    """
    Decorator that registers a widget configuration in the WIDGETS dictionary.
    
    Args:
        widget_config (dict): The widget configuration to add to the WIDGETS 
            dictionary. This should follow the same structure as other entries 
            in WIDGETS.
    
    Returns:
        function: The decorated function.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Call the original function
            return await func(*args, **kwargs)
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Call the original function
            return func(*args, **kwargs)
        
        # Extract the endpoint from the widget_config
        endpoint = widget_config.get("endpoint")
        if endpoint:
            # Add an id field to the widget_config if not already present
            if "id" not in widget_config:
                widget_config["id"] = endpoint
            
            WIDGETS[endpoint] = widget_config
        
        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def add_template(template_name: str):
    """
    Function that adds a template from a JSON file in the templates directory
    to the TEMPLATES dictionary.
    
    Args:
        template_name (str): The name of the template file (without .json 
            extension)
    
    Returns:
        bool: True if template was successfully added, False otherwise
    """
    template_path = os.path.join(Path(__file__).parent.parent.resolve(), "templates", f"{template_name}.json")
    
    # Check if file exists
    if not os.path.exists(template_path):
        print(f"Template file not found: {template_path}")
        return False
    
    # Check if JSON is valid
    try:
        with open(template_path, 'r') as f:
            template_data = json.load(f)
            # Register the template in the TEMPLATES dictionary
            TEMPLATES[template_name] = template_data
            return True
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in template {template_name}: {e}")
        return False
    except Exception as e:
        print(f"Error loading template {template_name}: {e}")
        return False


def load_agent_config(template_name: str = "agents"):
    """
    Function that loads the agent configuration from a JSON file in the templates directory.
    
    Args:
        template_name (str): The name of the template file (without .json 
            extension)
    
    Returns:
        str: JSON string containing the agent configuration
    """
    template_path = os.path.join(Path(__file__).parent.parent.resolve(), "templates", f"{template_name}.json")
    
    # Check if file exists
    if not os.path.exists(template_path):
        print(f"Template file not found: {template_path}")
        return False
    
    # Check if JSON is valid
    try:
        with open(template_path, 'r') as f:
            template_data = json.load(f)
            # Register the template in the TEMPLATES dictionary
            return template_data
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in template {template_name}: {e}")
        return False
    except Exception as e:
        print(f"Error loading template {template_name}: {e}")
        return False
