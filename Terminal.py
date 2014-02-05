import sublime
import sublime_plugin
import os
import sys
import subprocess
import locale

if os.name == 'nt':
    try:
        import _winreg
    except (ImportError):
        import winreg as _winreg
    from ctypes import windll, create_unicode_buffer

class NotFoundError(Exception):
    pass


if sys.version_info >= (3,):
    installed_dir, _ = __name__.split('.')
else:
    installed_dir = os.path.basename(os.getcwd())


class TerminalSelector():
    default = None

    @staticmethod
    def get():
        settings = sublime.load_settings('Terminal.sublime-settings')
        package_dir = os.path.join(sublime.packages_path(), installed_dir)

        terminal = settings.get('terminal')
        if terminal:
            dir, executable = os.path.split(terminal)
            if not dir:
                joined_terminal = os.path.join(package_dir, executable)
                if os.path.exists(joined_terminal):
                    terminal = joined_terminal
                    if not os.access(terminal, os.X_OK):
                        os.chmod(terminal, 0o755)
            return terminal

        if TerminalSelector.default:
            return TerminalSelector.default

        default = None

        if os.name == 'nt':
                default = os.path.join(package_dir, 'Gitbash.bat')
        elif sys.platform == 'darwin':
            default = os.path.join(package_dir, 'Terminal.sh')
            if not os.access(default, os.X_OK):
                os.chmod(default, 0o755)

        else:
            ps = 'ps -eo comm | grep -E "gnome-session|ksmserver|' + \
                'xfce4-session" | grep -v grep'
            wm = [x.replace("\n", '') for x in os.popen(ps)]
            if wm:
                if wm[0] == 'gnome-session':
                    default = 'gnome-terminal'
                elif wm[0] == 'xfce4-session':
                    default = 'terminal'
                elif wm[0] == 'ksmserver':
                    default = 'konsole'
            if not default:
                default = 'xterm'

        TerminalSelector.default = default
        return default


class TerminalCommand():
    def get_path(self, paths):
        if paths:
            return paths[0]
        elif self.window.active_view():
            return self.window.active_view().file_name()
        elif self.window.folders():
            return self.window.folders()[0]
        else:
            sublime.error_message('Terminal: No place to open terminal to')
            return False

    def run_terminal(self, dir_, parameters):
        try:
            if not dir_:
                raise NotFoundError('The file open in the selected view has ' +
                    'not yet been saved')
            for k, v in enumerate(parameters):
                parameters[k] = v.replace('%CWD%', dir_)
            args = [TerminalSelector.get()]
            args.extend(parameters)
            encoding = locale.getpreferredencoding(do_setlocale=True)
            if sys.version_info >= (3,):
                cwd = dir_
            else:
                cwd = dir_.encode(encoding)
            subprocess.Popen(args, cwd=cwd)

        except (OSError) as exception:
            print(str(exception))
            sublime.error_message('Terminal: The terminal ' +
                TerminalSelector.get() + ' was not found')
        except (Exception) as exception:
            sublime.error_message('Terminal: ' + str(exception))


class OpenTerminalCommand(sublime_plugin.WindowCommand, TerminalCommand):
    def run(self, paths=[], parameters=None):
        path = self.get_path(paths)
        if not path:
            return

        if parameters == None:
            settings = sublime.load_settings('Terminal.sublime-settings')
            parameters = settings.get('parameters')

        if not parameters:
            parameters = []

        if os.path.isfile(path):
            path = os.path.dirname(path)

        self.run_terminal(path, parameters)


class OpenTerminalProjectFolderCommand(sublime_plugin.WindowCommand,
        TerminalCommand):
    def run(self, paths=[], parameters=None):
        path = self.get_path(paths)
        if not path:
            return

        folders = [x for x in self.window.folders() if path.find(x) == 0][0:1]

        command = OpenTerminalCommand(self.window)
        command.run(folders, parameters=parameters)