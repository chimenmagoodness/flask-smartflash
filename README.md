# Flask SmartFlash

A modern Flask extension for displaying beautiful flash messages with support for both toast notifications and modal popups with smooth animations.

## Features

- 🎯 **Two Display Methods**: Toast notifications and modal popups
- 🎨 **Beautiful Animations**: Smooth transitions and multiple animation styles
- 📱 **Responsive Design**: Works perfectly on mobile and desktop
- 🎭 **Multiple Categories**: Success, error, warning, and info messages
- ⚙️ **Highly Customizable**: Positions, durations, animations, and more
- 🔧 **Easy Integration**: Drop-in replacement for Flask's built-in flash system
- 🎪 **No Dependencies**: Pure CSS and JavaScript, no external libraries required

## Preview Images

### Toasts:
![SmartFlash Toast Preview  Success Image](images/taost%20success.PNG)
![SmartFlash Toast Preview  Error Image](images/toast%20error.PNG)
![SmartFlash Toast Preview  Info Image](images/toast%20info.PNG)
![SmartFlash Toast Preview  Warning Image](toast%20warning.PNG)

### Pop Ups:
![SmartFlash Popup Preview  Success Image](images/popup%20success.PNG)
![SmartFlash Popup Preview  Error Image](images/popup%20error.PNG)
![SmartFlash Popup Preview  Info Image](images/popup%20info.PNG)
![SmartFlash Popup Preview  Warning Image](images/popup%20warnings.PNG)


## Installation

### Method 1: Install from PyPI (Recommended)

```bash
pip install flask-smartflash
```

### Method 2: Install from Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/flask-smartflash.git
cd flask-smartflash
```

2. Install the package:
```bash
pip install -e .
```

### Method 3: Manual Installation

1. Download the package files
2. Copy the `smartflash` folder to your project directory
3. Install Flask if not already installed:
```bash
pip install Flask
```

## Quick Start

### 1. Basic Setup

```python

from flask import Flask, render_template, redirect, url_for
from smartflash import SmartFlash

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Initialize SmartFlash
smartflash = SmartFlash(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/toast/<category>')
def show_toast(category):
    messages = {
        'success': 'Operation completed successfully!',
        'error': 'An error occurred while processing your request.',
        'warning': 'Please check your input and try again.',
        'info': 'Here is some useful information for you.'
    }
    
    smartflash(messages.get(category, 'Default message'), category, method='toast', 
          position='top-right', duration=4000, animation='fadeIn', exit_animation='zoomOut')
    return redirect(url_for('index'))

@app.route('/popup/<category>')
def show_popup(category):
    messages = {
        'success': 'Your changes have been saved successfully!',
        'error': 'Unable to process your request. Please try again later.',
        'warning': 'Are you sure you want to continue with this action?',
        'info': 'This is an informational message with important details.'
    }
    
    smartflash(messages.get(category, 'Default message'), category, method='popup',
          title=category.capitalize() + ' Message',
          animation='bounceIn',
          confirm_text='Got it!')
    return redirect(url_for('index'))


# or you can use this method

@app.route('/success')
def success():
    smartflash( 'Operation completed successfully!', 'success', method='toast')
    return redirect(url_for('index'))

@app.route('/error')
def error():
    smartflash('An error occurred!', 'error', method='popup')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)


```

### 2. Template Setup

Create `templates/base.html`:

```html

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SmartFlash Demo</title>
    {{ smartflash_include_css() }}
  </head>
  <body>
    {% block content %}{% endblock %}

    <!-- Include SmartFlash messages -->
    {{ smartflash_render() }}
  </body>
</html>

```

Create `templates/index.html`:

```html
{% extends "base.html" %}

{% block content %}
<div style="padding: 50px; text-align: center;">
    <h1>SmartFlash Demo</h1>

    <h2>Toast Notifications</h2>
    <a href="/toast/success" class="btn">Success Toast</a>
    <a href="/toast/error" class="btn">Error Toast</a>
    <a href="/toast/warning" class="btn">Warning Toast</a>
    <a href="/toast/info" class="btn">Info Toast</a>

    <h2>Modal Popups</h2>
    <a href="/popup/success" class="btn">Success Popup</a>
    <a href="/popup/error" class="btn">Error Popup</a>
    <a href="/popup/warning" class="btn">Warning Popup</a>
    <a href="/popup/info" class="btn">Info Popup</a>

    <h2>Calling by Function</h2>
    <a href="{{ url_for('success') }}" class="btn">Success Toast </a>
    <a href="{{ url_for('error') }}" class="btn">Error Popup </a>
</div>

<style>
    .btn {
        display: inline-block;
        padding: 10px 20px;
        margin: 5px;
        background: #007bff;
        color: white;
        text-decoration: none;
        border-radius: 5px;
        transition: background 0.3s;
    }

    .btn:hover {
        background: #0056b3;
    }
</style>
{% endblock %}

```

## API Reference

### SmartFlash Class

#### `SmartFlash(app=None)`

Initialize the SmartFlash extension.

**Parameters:**
- `app` (Flask, optional): Flask application instance

#### `init_app(app)`

Initialize the extension with a Flask app (for factory pattern).

**Parameters:**
- `app` (Flask): Flask application instance

#### `flash(message, category='info', method=None, **kwargs)`

Flash a message using SmartFlash.

**Parameters:**
- `message` (str): The message to display
- `category` (str): Message category ('success', 'error', 'warning', 'info')
- `method` (`str`, optional): Display method. Either `'toast'` or `'popup'`. Defaults to `'toast'`.
- `position` (`str`, optional): Position of the toast on screen (e.g., `'top-right'`, `'bottom-left'`). Only applicable for toast. Defaults to `'top-right'`.
- `duration` (`int`, optional): Duration in milliseconds before the message disappears. Defaults to `4000`.
- `animation` (`str`, optional): Entry animation class. Defaults to `'fadeIn'`.
- `exit_animation` (`str`, optional): Exit animation class. Defaults to `'fadeOut'`.
- `**kwargs`: Additional customization options (e.g., `overlay_click_close=True`, `close_button=True`).

**Available Animations:**

You can use any of the following animation names for the `animation` or `exit_animation` parameters:

- `fadeIn`
- `slideIn`
- `bounceIn`
- `zoomIn`
- `rotateIn`
- `flipIn`
- `elasticIn`
- `slideInLeft`
- `slideInRight`
- `expandIn`
- `glowIn`
- `swingIn`
- `rollIn`
- `morphIn`


> 🔁 For exit animations, You can use any of the following animation names for the `exit_animation` parameters.
- `fadeOut`
- `slideOut`
- `zoomOut`


---

### Flash Methods

#### Toast Notifications

```python
flash('Message', 'success', method='toast', 
      position='top-right', duration=5000)
```

**Toast Options:**
- `position`: 'top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center'
- `duration`: Duration in milliseconds (default: 5000)

#### Modal Popups

```python
flash('Message', 'error', method='popup',
      title='Error', animation='bounceIn', confirm_text='OK')
```

**Popup Options:**
- `title`: Custom title for the popup
- `animation`: 'fadeIn', 'slideIn', 'bounceIn'
- `confirm_text`: Text for the confirm button
- exit_animation` (`str`, optional): Exit animation class. Defaults to `'fadeOut'`.

### Template Functions

#### `smartflash_include_css()`

Include SmartFlash CSS styles in your template.

```html
{{ smartflash_include_css() }}
```

#### `smartflash_render()`

Render SmartFlash messages in your template.

```html
<head>
    {{ smartflash_include_css() }}
</head>

<body>
    {% block content %}{% endblock %}

    <!-- Include SmartFlash messages -->
    {{ smartflash_render() }}
  </body>
```

## Configuration

This is optional but you can add these configuration options to your Flask app:

```python
app.config['SMARTFLASH_DEFAULT_METHOD'] = 'toast'  # Default: 'toast'
app.config['SMARTFLASH_TOAST_POSITION'] = 'top-right'  # Default: 'top-right'
app.config['SMARTFLASH_TOAST_DURATION'] = 5000  # Default: 5000ms
app.config['SMARTFLASH_POPUP_ANIMATION'] = 'fadeIn'  # Default: 'fadeIn'
```

## Advanced Usage

### Custom Styling

You can override the default styles by adding your own CSS after including SmartFlash CSS:

```html
{{ smartflash_include_css() }}
<style>
.smartflash-success {
    background: #custom-green !important;
}
</style>
```

### Multiple Messages

```python
@app.route('/multiple')
def multiple():
    smartflash('First message', 'info', method='toast', position='top-left')
    smartflash('Second message', 'success', method='toast', position='top-right')
    smartflash('Important alert', 'warning', method='popup')
    return redirect(url_for('index'))
```

### Conditional Flash Messages

```python
@app.route('/process')
def process():
    try:
        # Your processing logic here
        result = some_operation()
        smartflash('Operation successful!', 'success', method='toast')
    except ValueError as e:
        smartflash(f'Validation error: {str(e)}', 'warning', method='popup')
    except Exception as e:
        smartflash('An unexpected error occurred.', 'error', method='popup')
    
    return redirect(url_for('index'))
```

### AJAX Integration

For AJAX requests, you can return flash data as JSON:

```python
from flask import jsonify

@app.route('/api/action', methods=['POST'])
def api_action():
    try:
        # Your logic here
        return jsonify({
            'success': True,
            'message': 'Action completed!',
            'flash': {
                'message': 'Action completed successfully!',
                'category': 'success',
                'method': 'toast'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'smartflash': {
                'message': 'Action failed!',
                'category': 'error',
                'method': 'popup'
            }
        }), 400
```

## Package Structure

```
smartflash/
├── __init__.py          # Main SmartFlash class and functionality
├── README.md           # This documentation
└── setup.py           # Package setup configuration

templates/              # Example templates
├── base.html
└── index.html

examples/               # Example applications
└── basic_app.py       # Complete example application
```

## Browser Support

SmartFlash works with all modern browsers:

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Troubleshooting

### Messages Not Appearing

1. Make sure you've included the CSS and render functions in your template:
```html
<!-- Make sure your base template has this  -->
{{ smartflash_include_css() }} <!-- Make sure this is in the head tag  -->
{{ smartflash_render() }} <!-- And this is in the body  -->

<!-- and you have extended your base.html in all your html.  -->
{% extends "base.html" %}
```

2. Ensure your Flask app has a secret key configured:
```python
app.secret_key = 'your-secret-key'
```

### Styling Issues

1. Check that SmartFlash CSS is loaded before any custom CSS
2. Use `!important` to override specific styles if needed
3. Clear browser cache if styles aren't updating

### JavaScript Errors

1. Make sure templates are properly structured with opening and closing HTML tags
2. Check browser console for any JavaScript errors
3. Ensure no conflicting JavaScript libraries

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Toast notifications support
- Modal popup support
- Multiple animation styles
- Responsive design
- Full customization options

## Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Look through existing issues on GitHub
3. Create a new issue with detailed information about your problem

## Examples

Check out the `examples/` directory for complete working examples demonstrating all features of SmartFlash.
