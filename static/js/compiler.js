// C Syntax Checker - Compiler Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize CodeMirror
    const textarea = document.getElementById('codeEditor');
    const editor = CodeMirror.fromTextArea(textarea, {
        mode: 'text/x-csrc',
        theme: 'monokai',
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        lineWrapping: false,
        autofocus: true,
        extraKeys: {
            'Ctrl-Enter': function() {
                checkCode();
            }
        }
    });

    // Sample code snippets
    const samples = {
        good1: `#include <stdio.h>
int main() {
    int x = 5;
    printf("x=%d\\n", x);
    return 0;
}
`,
        good2: `#include <stdio.h>
void greet() {
    printf("Hello\\n");
}
int main() {
    greet();
    return 0;
}
`,
        bad1: `int main() {
    int 1x = 5;
    char my-var = 'a';
    return 0;
}
`,
        bad2: `#include <stdio.h>
int main() {
    char *s = "hello;
    printf("%s\\n", s);
    return 0;
}
`,
        bad3: `#include <stdio.h>
int main() {
    Infinate x = 0;
    printf("%d\\n", x);
    return 0;
}
`
    };

    // DOM Elements
    const checkBtn = document.getElementById('checkBtn');
    const mobileCheckBtn = document.getElementById('mobileCheckBtn');
    const clearBtn = document.getElementById('clearBtn');
    const mobileClearBtn = document.getElementById('mobileClearBtn');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    const sampleBtn = document.getElementById('sampleBtn');
    const mobileSampleBtn = document.getElementById('mobileSampleBtn');
    const sampleMenu = document.getElementById('sampleMenu');
    const resultsContent = document.getElementById('resultsContent');
    const errorCount = document.getElementById('errorCount');
    const importBtn = document.getElementById('importBtn');
    const mobileImportBtn = document.getElementById('mobileImportBtn');
    const fileInput = document.getElementById('fileInput');

    // Check code function
    function checkCode() {
        const code = editor.getValue().trim();

        if (!code) {
            showNotification('Please enter C code before checking.', 'warning');
            return;
        }

        // Show loading state
        resultsContent.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>Checking code...</span>
            </div>
        `;

        // Make API call
        fetch('/api/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: code })
        })
        .then(response => response.json())
        .then(data => {
            displayResults(data.errors);
        })
        .catch(error => {
            console.error('Error:', error);
            resultsContent.innerHTML = `
                <div class="no-errors" style="color: #f44747;">
                    <div class="no-errors-icon">ERROR</div>
                    <div class="no-errors-text">Error checking code</div>
                    <p style="color: #8892a0; margin-top: 8px;">${error.message || 'Please try again'}</p>
                </div>
            `;
        });
    }

    // Display results
    function displayResults(errors) {
        const errorCountVal = errors.length;

        // Update error count badge
        errorCount.style.display = 'inline-flex';
        errorCount.textContent = errorCountVal;

        if (errorCountVal === 0) {
            errorCount.textContent = 'OK';
        } else if (errorCountVal <= 3) {
            errorCount.className = 'error-count warning';
        } else {
            errorCount.className = 'error-count error';
        }

        if (errors.length === 0) {
            resultsContent.innerHTML = `
                <div class="no-errors fade-in">
                    <div class="no-errors-icon">OK</div>
                    <div class="no-errors-text">No errors detected</div>
                    <p style="color: #8892a0; margin-top: 8px;">Your code looks good!</p>
                </div>
            `;
            downloadReportBtn.style.display = 'none';
            return;
        }

        // Show download report button
        downloadReportBtn.style.display = 'block';

        // Build error cards HTML
        let html = '';
        errors.forEach(function(error, index) {
            const severity = getSeverity(error.type);
            const severityLabel = severity.charAt(0).toUpperCase() + severity.slice(1);
            html += `
                <div class="error-card ${severity} fade-in" data-line="${error.line || ''}" style="animation-delay: ${index * 0.05}s">
                    <div class="error-card-header">
                        <span class="error-type-tag">${severityLabel}</span>
                        <span class="error-type">${error.type}</span>
                        ${error.line ? `<span class="error-line">Line ${error.line}</span>` : ''}
                    </div>
                    <div class="error-card-body">
                        <div class="error-message">${error.message}</div>
                    </div>
                </div>
            `;
        });

        resultsContent.innerHTML = html;

        // Add click handlers to error cards
        document.querySelectorAll('.error-card').forEach(function(card) {
            card.addEventListener('click', function() {
                const line = this.dataset.line;
                if (line) {
                    goToLine(parseInt(line));
                }
            });
        });
    }

    // Get severity based on error type
    function getSeverity(errorType) {
        const criticalTypes = ['Invalid variable name', 'Missing semicolon', 'Unclosed quote', 'Unclosed bracket', 'Mismatched bracket', 'Missing include', 'Include error', 'Missing return type'];
        const warningTypes = ['Incorrect keyword', 'Invalid operator'];

        if (criticalTypes.some(t => errorType && errorType.includes(t))) {
            return 'critical';
        } else if (warningTypes.some(t => errorType && errorType.includes(t))) {
            return 'warning';
        }
        return 'info';
    }

    // Go to specific line in editor
    function goToLine(lineNum) {
        editor.focus();
        editor.setCursor({ line: lineNum - 1, ch: 0 });
        const coords = editor.charCoords({ line: lineNum - 1, ch: 0 }, 'local');
        editor.scrollTo(null, coords.top - 100);
    }

    // Clear editor
    function clearEditor() {
        editor.setValue('');
        resultsContent.innerHTML = `
            <div class="no-errors">
                <div class="no-errors-icon">OK</div>
                <div class="no-errors-text">No errors detected</div>
                <p style="color: #8892a0; margin-top: 8px;">Enter C code and click "Check Code"</p>
            </div>
        `;
        errorCount.style.display = 'none';
        downloadReportBtn.style.display = 'none';
    }

    // Copy code to clipboard
    function copyCode() {
        const code = editor.getValue();
        navigator.clipboard.writeText(code).then(function() {
            showNotification('Code copied to clipboard!', 'success');
        }).catch(function() {
            showNotification('Failed to copy code', 'error');
        });
    }

    // Download code as .c file
    function downloadCode() {
        const code = editor.getValue();
        if (!code.trim()) {
            showNotification('No code to download', 'warning');
            return;
        }

        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'code.c';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Download error report
    function downloadReport() {
        const code = editor.getValue();
        const errors = document.querySelectorAll('.error-card');
        let report = '=== C Syntax Checker Report ===\n';
        report += 'Generated on: ' + new Date().toLocaleString() + '\n\n';
        
        report += '--- Source Code ---\n';
        report += code + '\n\n';
        
        report += '--- Analysis Results ---\n';
        report += `Total Issues Found: ${errors.length}\n`;
        report += '----------------------------\n\n';

        errors.forEach(function(err, i) {
            const type = err.querySelector('.error-type').textContent;
            const line = err.querySelector('.error-line');
            const message = err.querySelector('.error-message').textContent;
            report += `${i + 1}. ${type}${line ? ' (' + line.textContent + ')' : ''}\n`;
            report += `   Message: ${message}\n\n`;
        });

        const blob = new Blob([report], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'syntax_report.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Show notification
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 24px;
            background: ${type === 'success' ? '#4ec9b0' : type === 'error' ? '#f44747' : '#dcdcaa'};
            color: #0b0f12;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(function() {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(function() {
                document.body.removeChild(notification);
            }, 300);
        }, 2000);
    }

    // Load sample code
    function loadSample(sampleName) {
        const code = samples[sampleName];
        if (code) {
            editor.setValue(code);
            checkCode();
            closeDropdown();
        }
    }

    // Toggle dropdown
    function toggleDropdown() {
        sampleMenu.classList.toggle('open');
    }

    function closeDropdown() {
        sampleMenu.classList.remove('open');
    }

    // Event Listeners
    checkBtn.addEventListener('click', checkCode);
    mobileCheckBtn.addEventListener('click', checkCode);
    clearBtn.addEventListener('click', clearEditor);
    mobileClearBtn.addEventListener('click', clearEditor);
    importBtn.addEventListener('click', function() {
        fileInput.click();
    });
    mobileImportBtn.addEventListener('click', function() {
        fileInput.click();
    });
    fileInput.addEventListener('change', function(e) {
        fileInput.click();
    });
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                editor.setValue(event.target.result);
                showNotification('File imported successfully!', 'success');
            };
            reader.onerror = function() {
                showNotification('Error reading file.', 'error');
            };
            reader.readAsText(file);
        }
        fileInput.value = '';
    });
    copyBtn.addEventListener('click', copyCode);
    downloadBtn.addEventListener('click', downloadCode);
    downloadReportBtn.addEventListener('click', downloadReport);
    sampleBtn.addEventListener('click', toggleDropdown);
    mobileSampleBtn.addEventListener('click', function() {
        const menu = document.createElement('div');
        menu.className = 'mobile-sample-menu';
        menu.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 200;
        `;
        menu.innerHTML = `
            <div style="background: #0f1720; border-radius: 8px; padding: 16px; min-width: 250px;">
                <h3 style="color: #e6eef6; margin-bottom: 16px;">Load Sample</h3>
                ${Object.keys(samples).map(key => `
                    <button class="sample-option" data-sample="${key}" style="
                        display: block;
                        width: 100%;
                        padding: 12px 16px;
                        margin: 8px 0;
                        background: #1a1f26;
                        border: 1px solid #2d333b;
                        border-radius: 4px;
                        color: #e6eef6;
                        text-align: left;
                        cursor: pointer;
                    ">${key.replace('good', 'Valid ').replace('bad', 'Error ').replace(/(\d+)/g, '#$1')}</button>
                `).join('')}
                <button id="closeMobileSample" style="
                    margin-top: 16px;
                    width: 100%;
                    padding: 12px;
                    background: transparent;
                    border: 1px solid #2d333b;
                    border-radius: 4px;
                    color: #8892a0;
                    cursor: pointer;
                ">Cancel</button>
            </div>
        `;

        document.body.appendChild(menu);

        menu.querySelectorAll('.sample-option').forEach(function(btn) {
            btn.addEventListener('click', function() {
                loadSample(this.dataset.sample);
                document.body.removeChild(menu);
            });
        });

        document.getElementById('closeMobileSample').addEventListener('click', function() {
            document.body.removeChild(menu);
        });

        menu.addEventListener('click', function(e) {
            if (e.target === menu) {
                document.body.removeChild(menu);
            }
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!sampleBtn.contains(e.target) && !sampleMenu.contains(e.target)) {
            closeDropdown();
        }
    });

    // Sample menu item click handlers
    sampleMenu.querySelectorAll('.dropdown-item').forEach(function(item) {
        item.addEventListener('click', function() {
            loadSample(this.dataset.sample);
        });
    });

    // Add slideIn/slideOut animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // Mobile menu toggle
    const menuToggle = document.getElementById('menuToggle');
    const nav = document.querySelector('.nav');

    if (menuToggle && nav) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('open');
        });

        // Close nav when clicking a link
        nav.querySelectorAll('.nav-link').forEach(function(link) {
            link.addEventListener('click', function() {
                nav.classList.remove('open');
            });
        });
    }

    // Focus editor on Ctrl+L
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
            e.preventDefault();
            editor.focus();
        }
    });

    // Auto-resize editor on window resize
    window.addEventListener('resize', function() {
        editor.refresh();
    });
});