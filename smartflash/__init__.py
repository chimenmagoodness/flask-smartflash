from flask import session, request, Markup
import json
import uuid

class SmartFlash:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.jinja_env.globals['smartflash_render'] = self.render
        app.jinja_env.globals['smartflash_include_css'] = self.include_css
        app.jinja_env.globals['smartflash_include_js'] = self.include_js
        
        # Set default configuration
        app.config.setdefault('SMARTFLASH_DEFAULT_METHOD', 'toast')
        app.config.setdefault('SMARTFLASH_TOAST_POSITION', 'top-right')
        app.config.setdefault('SMARTFLASH_TOAST_DURATION', 5000)
        app.config.setdefault('SMARTFLASH_POPUP_ANIMATION', 'fadeIn')
    
    def flash(self, message, category='info', method=None, **kwargs):
        """
        Flash a message using SmartFlash
        
        Args:
            message (str): The message to display
            category (str): Message category (success, error, warning, info)
            method (str): Display method ('toast' or 'popup')
            **kwargs: Additional options for customization
        """
        if '_smartflash' not in session:
            session['_smartflash'] = []
        
        # Use default method if not specified
        if method is None:
            method = self.app.config.get('SMARTFLASH_DEFAULT_METHOD', 'toast')
        
        flash_data = {
            'id': str(uuid.uuid4()),
            'message': message,
            'category': category,
            'method': method,
            'options': kwargs
        }
        
        session['_smartflash'].append(flash_data)
        session.modified = True
    
    def get_flashed_messages(self, with_categories=False, category_filter=None):
        """Get and clear flashed messages"""
        flashes = session.pop('_smartflash', [])
        
        if category_filter:
            flashes = [f for f in flashes if f['category'] in category_filter]
        
        if with_categories:
            return [(f['category'], f) for f in flashes]
        return flashes
    
    def render(self):
        """Render SmartFlash messages"""
        messages = self.get_flashed_messages()
        if not messages:
            return ''
        
        html = '<div id="smartflash-container">'
        
        for msg in messages:
            if msg['method'] == 'toast':
                html += self._render_toast(msg)
            elif msg['method'] == 'popup':
                html += self._render_popup(msg)
        
        html += '</div>'
        html += self._render_js(messages)
        
        return Markup(html)
    
    def _render_toast(self, msg):
        """Render toast notification HTML"""
        position = msg['options'].get('position', 
            self.app.config.get('SMARTFLASH_TOAST_POSITION', 'top-right'))
        duration = msg['options'].get('duration', 
            self.app.config.get('SMARTFLASH_TOAST_DURATION', 5000))
        
        icon_map = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        }
        
        icon = icon_map.get(msg['category'], 'ℹ')
        
        return f'''
        <div id="{msg['id']}" class="smartflash-toast smartflash-{msg['category']} smartflash-{position}" 
             data-duration="{duration}" style="display: none;">
            <div class="smartflash-toast-content">
                <span class="smartflash-icon">{icon}</span>
                <span class="smartflash-message">{msg['message']}</span>
                <button class="smartflash-close" onclick="SmartFlash.closeToast('{msg['id']}')">&times;</button>
            </div>
        </div>
        '''
    
    def _render_popup(self, msg):
        """Render popup modal HTML"""
        animation = msg['options'].get('animation', 
            self.app.config.get('SMARTFLASH_POPUP_ANIMATION', 'fadeIn'))
        
        title = msg['options'].get('title', msg['category'].capitalize())
        confirm_text = msg['options'].get('confirm_text', 'OK')
        
        icon_map = {
            'success': '✓',
            'error': '✕',
            'warning': '⚠',
            'info': 'ℹ'
        }
        
        icon = icon_map.get(msg['category'], 'ℹ')
        
        return f'''
        <div id="{msg['id']}-overlay" class="smartflash-overlay" style="display: none;">
            <div class="smartflash-popup smartflash-{msg['category']} smartflash-{animation}">
                <div class="smartflash-popup-header">
                    <span class="smartflash-popup-icon">{icon}</span>
                    <h3 class="smartflash-popup-title">{title}</h3>
                </div>
                <div class="smartflash-popup-content">
                    <p>{msg['message']}</p>
                </div>
                <div class="smartflash-popup-footer">
                    <button class="smartflash-popup-btn smartflash-popup-confirm" 
                            onclick="SmartFlash.closePopup('{msg['id']}')">{confirm_text}</button>
                </div>
            </div>
        </div>
        '''
    
    def _render_js(self, messages):
        """Render JavaScript for SmartFlash"""
        return '''
        <script>
        if (typeof SmartFlash === 'undefined') {
            window.SmartFlash = {
                init: function() {
                    // Show toasts
                    document.querySelectorAll('.smartflash-toast').forEach(function(toast) {
                        SmartFlash.showToast(toast);
                    });
                    
                    // Show popups
                    document.querySelectorAll('.smartflash-overlay').forEach(function(overlay) {
                        SmartFlash.showPopup(overlay);
                    });
                },
                
                showToast: function(toast) {
                    toast.style.display = 'block';
                    setTimeout(function() {
                        toast.classList.add('smartflash-show');
                    }, 10);
                    
                    var duration = parseInt(toast.getAttribute('data-duration')) || 5000;
                    setTimeout(function() {
                        SmartFlash.closeToast(toast.id);
                    }, duration);
                },
                
                closeToast: function(id) {
                    var toast = document.getElementById(id);
                    if (toast) {
                        toast.classList.remove('smartflash-show');
                        setTimeout(function() {
                            toast.remove();
                        }, 300);
                    }
                },
                
                showPopup: function(overlay) {
                    overlay.style.display = 'flex';
                    setTimeout(function() {
                        overlay.querySelector('.smartflash-popup').classList.add('smartflash-show');
                    }, 10);
                },
                
                closePopup: function(id) {
                    var overlay = document.getElementById(id + '-overlay');
                    if (overlay) {
                        overlay.querySelector('.smartflash-popup').classList.remove('smartflash-show');
                        setTimeout(function() {
                            overlay.remove();
                        }, 300);
                    }
                }
            };
        }
        
        // Auto-initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', SmartFlash.init);
        } else {
            SmartFlash.init();
        }
        </script>
        '''
    
    def include_css(self):
        """Include SmartFlash CSS"""
        return Markup('''
        <style>
        /* SmartFlash Base Styles */
        .smartflash-toast {
            position: fixed;
            z-index: 9999;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 400px;
            min-width: 300px;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
        }
        
        .smartflash-toast.smartflash-show {
            opacity: 1;
            transform: translateY(0);
        }
        
        /* Toast Positions */
        .smartflash-top-right {
            top: 20px;
            right: 20px;
        }
        
        .smartflash-top-left {
            top: 20px;
            left: 20px;
        }
        
        .smartflash-bottom-right {
            bottom: 20px;
            right: 20px;
        }
        
        .smartflash-bottom-left {
            bottom: 20px;
            left: 20px;
        }
        
        .smartflash-top-center {
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
        }
        
        .smartflash-bottom-center {
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
        }
        
        /* Toast Content */
        .smartflash-toast-content {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .smartflash-icon {
            font-size: 18px;
            font-weight: bold;
        }
        
        .smartflash-message {
            flex: 1;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .smartflash-close {
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            opacity: 0.7;
            padding: 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .smartflash-close:hover {
            opacity: 1;
        }
        
        /* Toast Categories */
        .smartflash-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        
        .smartflash-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        
        .smartflash-warning {
            background: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffc107;
        }
        
        .smartflash-info {
            background: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #17a2b8;
        }
        
        /* Popup Overlay */
        .smartflash-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }
        
        /* Popup Modal */
        .smartflash-popup {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            opacity: 0;
            transform: scale(0.7);
            transition: all 0.3s ease;
        }
        
        .smartflash-popup.smartflash-show {
            opacity: 1;
            transform: scale(1);
        }
        
        /* Popup Header */
        .smartflash-popup-header {
            padding: 25px 25px 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        .smartflash-popup-icon {
            display: inline-block;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            line-height: 60px;
            font-size: 24px;
            color: white;
            margin-bottom: 15px;
        }
        
        .smartflash-popup.smartflash-success .smartflash-popup-icon {
            background: #28a745;
        }
        
        .smartflash-popup.smartflash-error .smartflash-popup-icon {
            background: #dc3545;
        }
        
        .smartflash-popup.smartflash-warning .smartflash-popup-icon {
            background: #ffc107;
            color: #333;
        }
        
        .smartflash-popup.smartflash-info .smartflash-popup-icon {
            background: #17a2b8;
        }
        
        .smartflash-popup-title {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
            color: #333;
        }
        
        /* Popup Content */
        .smartflash-popup-content {
            padding: 20px 25px;
            text-align: center;
        }
        
        .smartflash-popup-content p {
            margin: 0;
            font-size: 16px;
            line-height: 1.5;
            color: #666;
        }
        
        /* Popup Footer */
        .smartflash-popup-footer {
            padding: 15px 25px 25px;
            text-align: center;
        }
        
        .smartflash-popup-btn {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .smartflash-popup-confirm {
            background: #007bff;
            color: white;
        }
        
        .smartflash-popup-confirm:hover {
            background: #0056b3;
            transform: translateY(-1px);
        }
        
        /* Animations */
        .smartflash-fadeIn {
            animation: smartflashFadeIn 0.3s ease;
        }
        
        .smartflash-slideIn {
            animation: smartflashSlideIn 0.3s ease;
        }
        
        .smartflash-bounceIn {
            animation: smartflashBounceIn 0.5s ease;
        }
        
        @keyframes smartflashFadeIn {
            from { opacity: 0; transform: scale(0.7); }
            to { opacity: 1; transform: scale(1); }
        }
        
        @keyframes smartflashSlideIn {
            from { opacity: 0; transform: translateY(-50px) scale(0.7); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        
        @keyframes smartflashBounceIn {
            0% { opacity: 0; transform: scale(0.3); }
            40% { opacity: 1; transform: scale(1.05); }
            60% { transform: scale(0.95); }
            80% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        
        /* Responsive */
        @media (max-width: 480px) {
            .smartflash-toast {
                left: 10px !important;
                right: 10px !important;
                max-width: none;
                min-width: auto;
            }
            
            .smartflash-popup {
                margin: 20px;
                width: calc(100% - 40px);
            }
        }
        </style>
        ''')
    
    def include_js(self):
        """Include additional SmartFlash JavaScript if needed"""
        return Markup('')

# Convenience function for easy import
def flash(message, category='info', method=None, **kwargs):
    """Convenience function to flash messages"""
    from flask import current_app
    smartflash = current_app.extensions.get('smartflash')
    if smartflash:
        smartflash.flash(message, category, method, **kwargs)



