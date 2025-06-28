from flask import current_app, session, request
from markupsafe import Markup
import uuid
import threading
import weakref
from flask import appcontext_pushed

class SmartFlash:
    _instances = {}
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern per Flask app to ensure single registration."""
        try:
            app = current_app._get_current_object()
            app_id = id(app)
        except RuntimeError:
            # Not in app context, create temporary instance
            return super().__new__(cls)
        
        with cls._lock:
            if app_id not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[app_id] = instance
                instance._initialized = False
            return cls._instances[app_id]
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._initialized = True
        # Try to auto-register immediately if we're in an app context
        try:
            self._auto_register()
        except RuntimeError:
            # Not in app context yet, that's fine
            pass
    
    def _auto_register(self):
        """Ensure Jinja globals and config are injected only once per app."""
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            return  # Not in app context

        if not hasattr(app, '_smartflash_jinja_injected'):
            
            @app.context_processor
            def _inject_smartflash():
                return {
                    'smartflash_render': self.render,
                    'smartflash_include_css': self.include_css,
                    'smartflash_include_js': self.include_js,
                }

            # Register config defaults once
            app.config.setdefault('SMARTFLASH_DEFAULT_METHOD', 'toast')
            app.config.setdefault('SMARTFLASH_TOAST_POSITION', 'top-right')
            app.config.setdefault('SMARTFLASH_TOAST_DURATION', 5000)
            app.config.setdefault('SMARTFLASH_POPUP_ANIMATION', 'fadeIn')
            app.config.setdefault('SMARTFLASH_POPUP_EXIT_ANIMATION', 'fadeOut')
            app.config.setdefault('SMARTFLASH_TOAST_EXIT_ANIMATION', 'fadeOut')
            app.config.setdefault('SMARTFLASH_DEFAULT_OPTIONS', {})

            # Store reference in app extensions
            if not hasattr(app, 'extensions'):
                app.extensions = {}
            app.extensions['smartflash'] = self

            app._smartflash_jinja_injected = True

    def init_app(self, app):
        """Optional manual init for those who prefer it."""
        with app.app_context():
            self._auto_register()

    def __call__(self, message, category='info', method=None, **kwargs):
        return self.flash(message, category, method, **kwargs)

    def flash(self, message, category='info', method=None, **kwargs):
        self._auto_register()

        if '_smartflash' not in session:
            session['_smartflash'] = []

        config = current_app.config
        if method is None:
            method = config.get('SMARTFLASH_DEFAULT_METHOD', 'toast')

        flash_data = {
            'id': str(uuid.uuid4()),
            'message': message,
            'category': category,
            'method': method,
            'options': kwargs,
        }

        session['_smartflash'].append(flash_data)
        session.modified = True

    def get_flashed_messages(self, with_categories=False, category_filter=None):
        flashes = session.pop('_smartflash', [])

        if category_filter:
            flashes = [f for f in flashes if f['category'] in category_filter]

        if with_categories:
            return [(f['category'], f) for f in flashes]
        return flashes

    def render(self):
        self._auto_register()

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
        self._auto_register()
        
        config = current_app.config
        
        position = msg['options'].get('position', 
            config.get('SMARTFLASH_TOAST_POSITION', 'top-right'))
        duration = msg['options'].get('duration', 
            config.get('SMARTFLASH_TOAST_DURATION', 5000))
        animation = msg['options'].get('animation', 
            config.get('SMARTFLASH_POPUP_ANIMATION', 'fadeIn'))
        exit_animation = msg['options'].get('exit_animation', 
            config.get('SMARTFLASH_TOAST_EXIT_ANIMATION', 'fadeOut'))

        icon_map = {
            'success': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
            'error': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            'warning': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            'info': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
        }

        icon = icon_map.get(msg['category'], icon_map['info'])

        return f'''
            <div id="{msg['id']}" class="smartflash-toast smartflash-{msg['category']} smartflash-{position} smartflash-{animation}" 
                data-duration="{duration}" data-exit-animation="{exit_animation}" style="display: none;">
                <div class="smartflash-toast-content">
                    <div class="smartflash-icon">{icon}</div>
                    <span class="smartflash-message">{msg['message']}</span>
                    <button class="smartflash-close" onclick="SmartFlash.closeToast('{msg['id']}')">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="smartflash-progressbar">
                    <div class="smartflash-progress"></div>
                </div>
            </div>
        '''

    def _render_popup(self, msg):
        """Render popup modal HTML"""
        self._auto_register()
        
        config = current_app.config
        
        animation = msg['options'].get('animation', 
            config.get('SMARTFLASH_POPUP_ANIMATION', 'fadeIn'))
        exit_animation = msg['options'].get('exit_animation',
            config.get('SMARTFLASH_POPUP_EXIT_ANIMATION', 'fadeOut'))

        title = msg['options'].get('title', msg['category'].capitalize())
        confirm_text = msg['options'].get('confirm_text', 'OK')

        icon_map = {
            'success': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
            'error': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            'warning': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            'info': '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>'
        }

        icon = icon_map.get(msg['category'], icon_map['info'])

        return f'''
            <div id="{msg['id']}-overlay" class="smartflash-overlay" data-exit-animation="{exit_animation}" style="display: none;">
                <div class="smartflash-popup smartflash-{msg['category']} smartflash-{animation}">
                    <div class="smartflash-popup-header">
                        <div class="smartflash-popup-icon">{icon}</div>
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
                        document.querySelectorAll('.smartflash-toast').forEach(function(toast) {
                            SmartFlash.showToast(toast);
                        });

                        document.querySelectorAll('.smartflash-overlay').forEach(function(overlay) {
                            SmartFlash.showPopup(overlay);
                        });
                    },

                    showToast: function(toast) {
                        toast.style.display = 'block';

                        requestAnimationFrame(function () {
                            toast.classList.add('smartflash-show');

                            var progress = toast.querySelector('.smartflash-progress');
                            if (progress) {
                                var duration = parseInt(toast.getAttribute('data-duration')) || 5000;
                                progress.style.width = '0%';
                                progress.style.transition = `width ${duration}ms linear`;
                                progress.offsetWidth; // force reflow
                                progress.style.width = '100%';

                                let startTime = Date.now();
                                let remaining = duration;
                                let paused = false;

                                let closeTimeout = setTimeout(function () {
                                    SmartFlash.closeToast(toast.id);
                                }, duration);

                                // Pause on hover
                                toast.addEventListener('mouseenter', function () {
                                    if (!paused) {
                                        paused = true;
                                        let elapsed = Date.now() - startTime;
                                        remaining = duration - elapsed;

                                        // Get current width % before freezing
                                        const computed = window.getComputedStyle(progress);
                                        const widthPx = parseFloat(computed.width);
                                        const parentWidth = parseFloat(window.getComputedStyle(progress.parentElement).width);
                                        const currentPercent = (widthPx / parentWidth) * 100;

                                        progress.style.transition = 'none';
                                        progress.style.width = `${currentPercent}%`;

                                        clearTimeout(closeTimeout);
                                    }
                                });

                                // Resume on un-hover
                                toast.addEventListener('mouseleave', function () {
                                    if (paused) {
                                        paused = false;
                                        startTime = Date.now();

                                        progress.offsetWidth; // reflow
                                        progress.style.transition = `width ${remaining}ms linear`;
                                        progress.style.width = '100%';

                                        closeTimeout = setTimeout(function () {
                                            SmartFlash.closeToast(toast.id);
                                        }, remaining);
                                    }
                                });
                            }
                        });
                    },

                    closeToast: function(id) {
                        var toast = document.getElementById(id);
                        if (toast) {
                            // Get exit animation from data attribute or default to fadeOut
                            var exitAnimation = toast.dataset.exitAnimation || 'fadeOut';
                            
                            // Remove existing entry animations and show class
                            toast.className = toast.className.replace(/smartflash-\w+In/g, '');
                            toast.classList.remove('smartflash-show');
                            
                            // Add exit animation class
                            toast.classList.add(`smartflash-${exitAnimation}`);
                            
                            // Remove element after animation completes
                            setTimeout(function() {
                                if (toast.parentNode) {
                                    toast.remove();
                                }
                            }, 400); // Slightly longer to ensure animation completes
                        }
                    },

                    showPopup: function(overlay) {
                        overlay.style.display = 'flex';
                        requestAnimationFrame(function() {
                            overlay.classList.add('smartflash-show');
                            overlay.querySelector('.smartflash-popup').classList.add('smartflash-show');
                        });
                    },

                    closePopup: function(id) {
                        var overlay = document.getElementById(id + '-overlay');
                        if (overlay) {
                            // Get exit animation from data attribute or default to fadeOut
                            var exitAnimation = overlay.dataset.exitAnimation || 'fadeOut';
                            var popup = overlay.querySelector('.smartflash-popup');
                            
                            // Remove existing classes
                            overlay.classList.remove('smartflash-show');
                            if (popup) {
                                popup.classList.remove('smartflash-show');
                                
                                // Remove entry animations and add exit animation
                                popup.className = popup.className.replace(/smartflash-\w+In/g, '');
                                popup.classList.add(`smartflash-${exitAnimation}`);
                            }
                            
                            // Add overlay hide class for backdrop fade
                            overlay.classList.add('smartflash-hide');
                            
                            // Remove element after animation completes
                            setTimeout(function() {
                                if (overlay.parentNode) {
                                    overlay.remove();
                                }
                            }, 400); // Slightly longer to ensure animation completes
                        }
                    },

                    // Utility function to manually close toast with custom exit animation
                    closeToastWithAnimation: function(id, exitAnimation) {
                        var toast = document.getElementById(id);
                        if (toast) {
                            // Override the data attribute temporarily
                            toast.dataset.exitAnimation = exitAnimation;
                            SmartFlash.closeToast(id);
                        }
                    },

                    // Utility function to manually close popup with custom exit animation
                    closePopupWithAnimation: function(id, exitAnimation) {
                        var overlay = document.getElementById(id + '-overlay');
                        if (overlay) {
                            // Override the data attribute temporarily
                            overlay.dataset.exitAnimation = exitAnimation;
                            SmartFlash.closePopup(id);
                        }
                    }
                };
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', SmartFlash.init);
            } else {
                SmartFlash.init();
            }
            </script>
        '''
    
    
    def include_css(self):
        """Include SmartFlash CSS"""
        self._auto_register()
        
        config = current_app.config
        position = config.get('SMARTFLASH_TOAST_POSITION', 'top-right')
        return Markup('''
            <style>
                /* Toast Positioning Updates for Progress Bar */
                .smartflash-toast {
                    position: fixed;
                    z-index: 9999;
                    padding: 16px 20px;
                    border-radius: 16px;
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif;
                    max-width: 420px;
                    min-width: 320px;
                    opacity: 0;
                    transform: translateY(-24px) scale(0.95);
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    font-weight: 500;
                    will-change: transform, opacity;
                    overflow: hidden;
                }
                
                .smartflash-toast.smartflash-show {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
                
                .smartflash-toast.smartflash-hide {
                    opacity: 0;
                    transform: translateY(-12px) scale(0.98);
                    transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
                }
                
                /* Toast Positions */
                .smartflash-top-right {
                    top: 24px;
                    right: 24px;
                }
                
                .smartflash-top-left {
                    top: 24px;
                    left: 24px;
                }
                
                .smartflash-bottom-right {
                    bottom: 24px;
                    right: 24px;
                }
                
                .smartflash-bottom-left {
                    bottom: 24px;
                    left: 24px;
                }
                
                .smartflash-top-center {
                    top: 24px;
                    left: 50%;
                    transform: translateX(-50%) translateY(-24px) scale(0.95);
                }
                
                .smartflash-top-center.smartflash-show {
                    transform: translateX(-50%) translateY(0) scale(1);
                }
                
                .smartflash-bottom-center {
                    bottom: 24px;
                    left: 50%;
                    transform: translateX(-50%) translateY(24px) scale(0.95);
                }
                
                .smartflash-bottom-center.smartflash-show {
                    transform: translateX(-50%) translateY(0) scale(1);
                }
                
                /* Toast Content */
                .smartflash-toast-content {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                
                .smartflash-icon {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 24px;
                    height: 24px;
                    flex-shrink: 0;
                    animation: smartflashIconPulse 2s ease-in-out infinite;
                }
                
                .smartflash-icon svg {
                    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-toast:hover .smartflash-icon svg {
                    transform: scale(1.1);
                }
                
                .smartflash-message {
                    flex: 1;
                    font-size: 14px;
                    line-height: 1.5;
                    font-weight: 500;
                }
                
                .smartflash-close {
                    background: none;
                    border: none;
                    cursor: pointer;
                    opacity: 0.6;
                    padding: 4px;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    flex-shrink: 0;
                }
                
                .smartflash-close:hover {
                    opacity: 1;
                    background: rgba(0, 0, 0, 0.08);
                    transform: scale(1.1);
                }
                
                /* Progress Bar - Bottom Border Style */
                .smartflash-progressbar {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: rgba(255, 255, 255, 0.15);
                    border-radius: 0 0 16px 16px;
                    overflow: hidden;
                }

                .smartflash-progress {
                    position: absolute;
                    top: 0;
                    left: 0;
                    bottom: 0;
                    width: 0%;
                    border-radius: 0 0 16px 16px;
                    transition: width cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                /* Toast Categories - Modern Glassmorphism */
                .smartflash-success {
                    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%);
                    color: #059669;
                    border-color: rgba(16, 185, 129, 0.3);
                }
                
                .smartflash-success .smartflash-progress {
                    background: linear-gradient(90deg, #10b981, #059669);
                    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
                }
                
                .smartflash-error {
                    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.1) 100%);
                    color: #dc2626;
                    border-color: rgba(239, 68, 68, 0.3);
                }
                
                .smartflash-error .smartflash-progress {
                    background: linear-gradient(90deg, #ef4444, #dc2626);
                    box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
                }
                
                .smartflash-warning {
                    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.1) 100%);
                    color: #d97706;
                    border-color: rgba(245, 158, 11, 0.3);
                }
                
                .smartflash-warning .smartflash-progress {
                    background: linear-gradient(90deg, #f59e0b, #d97706);
                    box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
                }
                
                .smartflash-info {
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.1) 100%);
                    color: #2563eb;
                    border-color: rgba(59, 130, 246, 0.3);
                }
                
                .smartflash-info .smartflash-progress {
                    background: linear-gradient(90deg, #3b82f6, #2563eb);
                    box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
                }
                
                /* Popup Overlay */
                .smartflash-overlay {
                    position: fixed;
                    top: 0; left: 0; width: 100%; height: 100%;
                    background: rgba(0, 0, 0, 0.4);
                    backdrop-filter: blur(8px);
                    -webkit-backdrop-filter: blur(8px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                    opacity: 0;
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-overlay.smartflash-show {
                    opacity: 1;
                }
                
                .smartflash-overlay.smartflash-hide {
                    opacity: 0;
                    transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
                }
                
                /* Popup Modal */
                .smartflash-popup {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 24px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 8px 20px rgba(0, 0, 0, 0.08);
                    max-width: 480px;
                    width: 90%;
                    max-height: 80vh;
                    overflow: hidden;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif;
                    opacity: 0;
                    transform: scale(0.9) translateY(20px);
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-popup.smartflash-show {
                    opacity: 1;
                    transform: scale(1) translateY(0);
                }
                
                .smartflash-popup.smartflash-hide {
                    opacity: 0;
                    transform: scale(0.95) translateY(12px);
                    transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
                }
                
                /* Popup Header */
                .smartflash-popup-header {
                    padding: 32px 32px 24px;
                    text-align: center;
                }
                
                .smartflash-popup-icon {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    margin-bottom: 20px;
                    background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.05));
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    animation: smartflashPopupIconFloat 3s ease-in-out infinite;
                }
                
                .smartflash-popup-icon svg {
                    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-popup:hover .smartflash-popup-icon svg {
                    transform: scale(1.1) rotate(5deg);
                }
                
                .smartflash-popup.smartflash-success .smartflash-popup-icon {
                    color: #059669;
                    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.1));
                    border-color: rgba(16, 185, 129, 0.3);
                }
                
                .smartflash-popup.smartflash-error .smartflash-popup-icon {
                    color: #dc2626;
                    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.1));
                    border-color: rgba(239, 68, 68, 0.3);
                }
                
                .smartflash-popup.smartflash-warning .smartflash-popup-icon {
                    color: #d97706;
                    background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.1));
                    border-color: rgba(245, 158, 11, 0.3);
                }
                
                .smartflash-popup.smartflash-info .smartflash-popup-icon {
                    color: #2563eb;
                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.1));
                    border-color: rgba(59, 130, 246, 0.3);
                }
                
                .smartflash-popup-title {
                    margin: 0;
                    font-size: 26px;
                    font-weight: 700;
                    color: #1f2937;
                    letter-spacing: -0.02em;
                }
                
                /* Popup Content */
                .smartflash-popup-content {
                    padding: 0 32px 24px;
                    text-align: center;
                }
                
                .smartflash-popup-content p {
                    margin: 0;
                    font-size: 16px;
                    line-height: 1.6;
                    color: #6b7280;
                    font-weight: 400;
                }
                
                /* Popup Footer */
                .smartflash-popup-footer {
                    padding: 0 32px 32px;
                    text-align: center;
                }
                
                .smartflash-popup-btn {
                    padding: 14px 32px;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    overflow: hidden;
                    min-width: 120px;
                }
                
                .smartflash-popup-btn::before {
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.3) 50%, transparent 70%);
                    transform: translateX(-100%);
                    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-popup-btn:hover::before {
                    transform: translateX(100%);
                }
                
                .smartflash-popup-confirm {
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                    color: white;
                    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
                }
                
                .smartflash-popup-confirm:hover {
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                    transform: translateY(-2px);
                    box-shadow: 0 8px 30px rgba(59, 130, 246, 0.4);
                }
                
                .smartflash-popup-confirm:active {
                    transform: translateY(0);
                    transition: transform 0.1s;
                }
                
                /* Enhanced Animations */
                .smartflash-fadeIn {
                    animation: smartflashFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-slideIn {
                    animation: smartflashSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .smartflash-bounceIn {
                    animation: smartflashBounceIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-zoomIn {
                    animation: smartflashZoomIn 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                }

                .smartflash-rotateIn {
                    animation: smartflashRotateIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-flipIn {
                    animation: smartflashFlipIn 0.7s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-elasticIn {
                    animation: smartflashElasticIn 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                }

                .smartflash-slideInLeft {
                    animation: smartflashSlideInLeft 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-slideInRight {
                    animation: smartflashSlideInRight 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-expandIn {
                    animation: smartflashExpandIn 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                }

                .smartflash-glowIn {
                    animation: smartflashGlowIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-swingIn {
                    animation: smartflashSwingIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-rollIn {
                    animation: smartflashRollIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                }

                .smartflash-morphIn {
                    animation: smartflashMorphIn 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                }

                
                @keyframes smartflashFadeIn {
                    from { 
                        opacity: 0; 
                        transform: scale(0.9) translateY(20px); 
                    }
                    to { 
                        opacity: 1; 
                        transform: scale(1) translateY(0); 
                    }
                }
                
                @keyframes smartflashSlideIn {
                    from { 
                        opacity: 0; 
                        transform: translateY(-60px) scale(0.9); 
                    }
                    to { 
                        opacity: 1; 
                        transform: translateY(0) scale(1); 
                    }
                }
                
                @keyframes smartflashBounceIn {
                    0% { 
                        opacity: 0; 
                        transform: scale(0.3) translateY(30px); 
                    }
                    30% { 
                        opacity: 1; 
                        transform: scale(1.05) translateY(-10px); 
                    }
                    60% { 
                        transform: scale(0.98) translateY(5px); 
                    }
                    80% { 
                        transform: scale(1.02) translateY(-2px); 
                    }
                    100% { 
                        transform: scale(1) translateY(0); 
                    }
                }

                .smartflash-fadeOut {
                    animation: smartflashFadeOut 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                }

                .smartflash-slideOut {
                    animation: smartflashSlideOut 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                }

                .smartflash-zoomOut {
                    animation: smartflashZoomOut 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
                }

                @keyframes smartflashFadeOut {
                    from {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                    to {
                        opacity: 0;
                        transform: scale(0.9) translateY(-20px);
                    }
                }

                @keyframes smartflashSlideOut {
                    from {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                    to {
                        opacity: 0;
                        transform: translateY(-60px) scale(0.9);
                    }
                }

                @keyframes smartflashZoomOut {
                    from {
                        opacity: 1;
                        transform: scale(1);
                    }
                    to {
                        opacity: 0;
                        transform: scale(0.5) rotate(-10deg);
                    }
                }

                /* Hover Enhancement Animations */
                .smartflash-hover-float:hover {
                    animation: smartflashFloat 2s ease-in-out infinite;
                }

                .smartflash-hover-pulse:hover {
                    animation: smartflashPulse 1.5s ease-in-out infinite;
                }

                @keyframes smartflashFloat {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-10px); }
                }

                @keyframes smartflashPulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                }
                
                /* Icon Animations */
                @keyframes smartflashIconPulse {
                    0%, 100% { 
                        opacity: 1; 
                        transform: scale(1);
                    }
                    50% { 
                        opacity: 0.8; 
                        transform: scale(1.05);
                    }
                }
                
                @keyframes smartflashPopupIconFloat {
                    0%, 100% { 
                        transform: translateY(0px) rotate(0deg);
                    }
                    33% { 
                        transform: translateY(-3px) rotate(1deg);
                    }
                    66% { 
                        transform: translateY(2px) rotate(-1deg);
                    }
                }

                @keyframes smartflashZoomIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.5) rotate(10deg);
                        filter: blur(4px);
                    }
                    60% {
                        opacity: 0.8;
                        transform: scale(1.02) rotate(-2deg);
                        filter: blur(1px);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1) rotate(0deg);
                        filter: blur(0);
                    }
                }

                @keyframes smartflashRotateIn {
                    0% {
                        opacity: 0;
                        transform: rotate(-180deg) scale(0.8);
                        transform-origin: center;
                    }
                    50% {
                        opacity: 0.7;
                        transform: rotate(-10deg) scale(1.05);
                    }
                    100% {
                        opacity: 1;
                        transform: rotate(0deg) scale(1);
                    }
                }

                @keyframes smartflashFlipIn {
                    0% {
                        opacity: 0;
                        transform: perspective(400px) rotateY(-90deg) scale(0.9);
                    }
                    40% {
                        opacity: 0.6;
                        transform: perspective(400px) rotateY(20deg) scale(1.02);
                    }
                    70% {
                        opacity: 0.9;
                        transform: perspective(400px) rotateY(-10deg) scale(1.01);
                    }
                    100% {
                        opacity: 1;
                        transform: perspective(400px) rotateY(0deg) scale(1);
                    }
                }

                @keyframes smartflashElasticIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.1) translateY(50px);
                    }
                    30% {
                        opacity: 0.8;
                        transform: scale(1.25) translateY(-20px);
                    }
                    50% {
                        transform: scale(0.85) translateY(10px);
                    }
                    70% {
                        transform: scale(1.1) translateY(-5px);
                    }
                    85% {
                        transform: scale(0.95) translateY(2px);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }

                @keyframes smartflashSlideInLeft {
                    0% {
                        opacity: 0;
                        transform: translateX(-100px) skewX(15deg);
                    }
                    60% {
                        opacity: 0.8;
                        transform: translateX(10px) skewX(-3deg);
                    }
                    100% {
                        opacity: 1;
                        transform: translateX(0) skewX(0deg);
                    }
                }

                @keyframes smartflashSlideInRight {
                    0% {
                        opacity: 0;
                        transform: translateX(100px) skewX(-15deg);
                    }
                    60% {
                        opacity: 0.8;
                        transform: translateX(-10px) skewX(3deg);
                    }
                    100% {
                        opacity: 1;
                        transform: translateX(0) skewX(0deg);
                    }
                }

                @keyframes smartflashExpandIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.1) translateY(20px);
                        border-radius: 50%;
                    }
                    50% {
                        opacity: 0.7;
                        transform: scale(1.15) translateY(-5px);
                        border-radius: 20%;
                    }
                    80% {
                        transform: scale(0.95) translateY(2px);
                        border-radius: 10%;
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                        border-radius: inherit;
                    }
                }

                @keyframes smartflashGlowIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.8);
                        box-shadow: 0 0 0 rgba(74, 144, 226, 0);
                        filter: brightness(0.5);
                    }
                    50% {
                        opacity: 0.8;
                        transform: scale(1.05);
                        box-shadow: 0 0 30px rgba(74, 144, 226, 0.6);
                        filter: brightness(1.3);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1);
                        box-shadow: 0 0 15px rgba(74, 144, 226, 0.2);
                        filter: brightness(1);
                    }
                }

                @keyframes smartflashSwingIn {
                    0% {
                        opacity: 0;
                        transform: rotate(20deg) translateY(-30px) scale(0.9);
                        transform-origin: top center;
                    }
                    30% {
                        opacity: 0.7;
                        transform: rotate(-15deg) translateY(-10px) scale(1.02);
                    }
                    60% {
                        opacity: 0.9;
                        transform: rotate(10deg) translateY(-2px) scale(1.01);
                    }
                    80% {
                        transform: rotate(-5deg) translateY(1px) scale(1);
                    }
                    100% {
                        opacity: 1;
                        transform: rotate(0deg) translateY(0) scale(1);
                    }
                }

                @keyframes smartflashRollIn {
                    0% {
                        opacity: 0;
                        transform: translateX(-100px) rotate(-120deg) scale(0.8);
                    }
                    50% {
                        opacity: 0.8;
                        transform: translateX(10px) rotate(20deg) scale(1.05);
                    }
                    80% {
                        transform: translateX(-5px) rotate(-5deg) scale(1.02);
                    }
                    100% {
                        opacity: 1;
                        transform: translateX(0) rotate(0deg) scale(1);
                    }
                }

                @keyframes smartflashMorphIn {
                    0% {
                        opacity: 0;
                        transform: scale(1, 0.1) skewX(45deg);
                        filter: blur(5px);
                    }
                    30% {
                        opacity: 0.6;
                        transform: scale(1.1, 0.8) skewX(-10deg);
                        filter: blur(2px);
                    }
                    60% {
                        opacity: 0.9;
                        transform: scale(0.95, 1.05) skewX(5deg);
                        filter: blur(1px);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1, 1) skewX(0deg);
                        filter: blur(0);
                    }
                }

                
                /* Dark Mode Support */
                @media (prefers-color-scheme: dark) {
                    .smartflash-popup {
                        background: rgba(17, 24, 39, 0.95);
                        border-color: rgba(75, 85, 99, 0.3);
                    }
                    
                    .smartflash-popup-title {
                        color: #f9fafb;
                    }
                    
                    .smartflash-popup-content p {
                        color: #d1d5db;
                    }
                    
                    .smartflash-close:hover {
                        background: rgba(255, 255, 255, 0.1);
                    }
                }
                
                /* Responsive Design */
                @media (max-width: 480px) {
                    .smartflash-toast {
                        left: 16px !important;
                        right: 16px !important;
                        max-width: none;
                        min-width: auto;
                        margin: 0;
                    }
                    
                    .smartflash-popup {
                        margin: 20px;
                        width: calc(100% - 40px);
                        border-radius: 20px;
                    }
                    
                    .smartflash-popup-header {
                        padding: 24px 24px 20px;
                    }
                    
                    .smartflash-popup-content {
                        padding: 0 24px 20px;
                    }
                    
                    .smartflash-popup-footer {
                        padding: 0 24px 24px;
                    }
                    
                    .smartflash-popup-icon {
                        width: 64px;
                        height: 64px;
                        margin-bottom: 16px;
                    }
                    
                    .smartflash-popup-title {
                        font-size: 22px;
                    }
                }
                
                /* Reduced Motion Support */
                @media (prefers-reduced-motion: reduce) {
                    .smartflash-toast,
                    .smartflash-popup,
                    .smartflash-overlay,
                    .smartflash-popup-btn {
                        transition: none;
                    }
                    
                    .smartflash-popup-btn::before {
                        display: none;
                    }
                }
            </style>
        ''')
    

    def include_js(self):
        self._auto_register()
        
        config = current_app.config
        duration = config.get('SMARTFLASH_TOAST_DURATION', 5000)
        
        """Include additional SmartFlash JavaScript if needed"""
        return Markup('')



smartflash = SmartFlash()


def _auto_init_app(sender, **extra):
    # This runs whenever an app context is pushed.
    try:
        smartflash._auto_register()
    except Exception:
        pass

# Attach to signal
appcontext_pushed.connect(_auto_init_app)
