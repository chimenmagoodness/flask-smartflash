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
