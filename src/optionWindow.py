# coding=utf-8
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tk_tools import TK_ROOT
from enum import Enum

from BEE2_config import GEN_OPTS
from tooltip import add_tooltip

import sound
import utils
import tk_tools
import srctools
import contextWin
import logWindow


class AfterExport(Enum):
    """Specifies what happens after exporting."""
    NORMAL = 0  # Stay visible
    MINIMISE = 1  # Minimise to tray
    QUIT = 2  # Quit the app.

UI = {}
PLAY_SOUND = BooleanVar(value=True, name='OPT_play_sounds')
KEEP_WIN_INSIDE = BooleanVar(value=True, name='OPT_keep_win_inside')
SHOW_LOG_WIN = BooleanVar(value=False, name='OPT_show_log_window')
LAUNCH_AFTER_EXPORT = BooleanVar(value=True, name='OPT_launch_after_export')
AFTER_EXPORT_ACTION = IntVar(
    value=AfterExport.MINIMISE.value,
    name='OPT_after_export_action',
)

refresh_callbacks = []  # functions called to apply settings.

VARS = {}


def reset_all_win():
    """Return all windows to their default positions.

    This is replaced by `UI.reset_panes`.
    """
    pass

win = Toplevel(TK_ROOT)
win.transient(master=TK_ROOT)
tk_tools.set_window_icon(win)
win.title(_('BEE2 Options'))
win.withdraw()


def show():
    """Display the option window."""
    win.deiconify()
    contextWin.hide_context()  # Ensure this closes
    utils.center_win(win)


def load():
    """Load the current settings from config."""
    for var in VARS.values():
        var.load()


def save():
    """Save settings into the config and apply them to other windows."""
    for var in VARS.values():
        var.save()

    sound.play_sound = PLAY_SOUND.get()
    utils.DISABLE_ADJUST = not KEEP_WIN_INSIDE.get()
    logWindow.set_visible(SHOW_LOG_WIN.get())

    for func in refresh_callbacks:
        func()


def clear_caches():
    """Wipe the cache times in configs.

     This will force package resources to be extracted again.
     """
    import gameMan
    import packageLoader

    restart_ok = messagebox.askokcancel(
        title=_('Allow Restart?'),
        message=_('Restart the BEE2 to re-extract packages?'),
    )

    if not restart_ok:
        return

    for game in gameMan.all_games:
        game.mod_times.clear()
        game.save()
    GEN_OPTS['General']['cache_time'] = '0'

    for pack_id in packageLoader.packages:
        packageLoader.PACK_CONFIG[pack_id]['ModTime'] = '0'

    save()  # Save any option changes..

    gameMan.CONFIG.save_check()
    GEN_OPTS.save_check()
    packageLoader.PACK_CONFIG.save_check()

    utils.restart_app()


def make_checkbox(
        frame,
        section,
        item,
        desc,
        default=False,
        var: BooleanVar=None,
        tooltip='',
        ):
    """Add a checkbox to the given frame which toggles an option.

    section and item are the location in GEN_OPTS for this config.
    If var is set, it'll be used instead of an auto-created variable.
    desc is the text put next to the checkbox.
    default is the default value of the variable, if var is None.
    frame is the parent frame.
    """
    if var is None:
        var = BooleanVar(
            value=default,
            name='opt_' + section.casefold() + '_' + item,
        )
    else:
        default = var.get()

    VARS[section, item] = var

    def save_opt():
        """Save the checkbox's values."""
        GEN_OPTS[section][item] = srctools.bool_as_int(
            var.get()
        )

    def load_opt():
        """Load the checkbox's values."""
        var.set(GEN_OPTS.get_bool(
            section,
            item,
            default,
        ))
    load_opt()

    var.save = save_opt
    var.load = load_opt
    widget = ttk.Checkbutton(
        frame,
        variable=var,
        text=desc,
    )

    if tooltip:
        add_tooltip(widget, tooltip)

    UI[section, item] = widget
    return widget


def init_widgets():
    """Create all the widgets."""
    UI['nbook'] = nbook = ttk.Notebook(
        win,

    )
    UI['nbook'].grid(
        row=0,
        column=0,
        padx=5,
        pady=5,
        sticky=NSEW,
    )
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)

    UI['fr_general'] = fr_general = ttk.Frame(
        nbook,
    )
    nbook.add(fr_general, text=_('General'))
    init_gen_tab(fr_general)

    UI['fr_win'] = fr_win = ttk.Frame(
        nbook,
    )
    nbook.add(fr_win, text=_('Windows'))
    init_win_tab(fr_win)

    UI['fr_dev'] = fr_dev = ttk.Frame(
        nbook,
    )
    nbook.add(fr_dev, text=_('Development'))
    init_dev_tab(fr_dev)

    ok_cancel = ttk.Frame(
        win
    )
    ok_cancel.grid(
        row=1,
        column=0,
        padx=5,
        pady=5,
        sticky=E,
    )

    def ok():
        save()
        win.withdraw()

    def cancel():
        win.withdraw()
        load()  # Rollback changes

    UI['ok_btn'] = ok_btn = ttk.Button(
        ok_cancel,
        text=_('OK'),
        command=ok,
    )
    UI['cancel_btn'] = cancel_btn = ttk.Button(
        ok_cancel,
        text=_('Cancel'),
        command=cancel,
    )
    ok_btn.grid(row=0, column=0)
    cancel_btn.grid(row=0, column=1)
    win.protocol("WM_DELETE_WINDOW", cancel)

    save()  # And ensure they are applied to other windows


def init_gen_tab(f):
    """Make widgets in the 'General' tab."""
    def load_after_export():
        """Read the 'After Export' radio set."""
        AFTER_EXPORT_ACTION.set(GEN_OPTS.get_int(
            'General',
            'after_export_action',
            AFTER_EXPORT_ACTION.get()
        ))

    def save_after_export():
        """Save the 'After Export' radio set."""
        GEN_OPTS['General']['after_export_action'] = str(AFTER_EXPORT_ACTION.get())

    after_export_frame = ttk.LabelFrame(
        f,
        text=_('After Export:'),
    )
    after_export_frame.grid(
        row=0,
        rowspan=2,
        column=0,
        sticky='NS',
        padx=(0, 10),
    )

    VARS['General', 'after_export_action'] = AFTER_EXPORT_ACTION
    AFTER_EXPORT_ACTION.load = load_after_export
    AFTER_EXPORT_ACTION.save = save_after_export
    load_after_export()

    exp_nothing = ttk.Radiobutton(
        after_export_frame,
        text=_('Do Nothing'),
        variable=AFTER_EXPORT_ACTION,
        value=AfterExport.NORMAL.value,
    )
    exp_minimise = ttk.Radiobutton(
        after_export_frame,
        text=_('Minimise BEE2'),
        variable=AFTER_EXPORT_ACTION,
        value=AfterExport.MINIMISE.value,
    )
    exp_quit = ttk.Radiobutton(
        after_export_frame,
        text=_('Quit BEE2'),
        variable=AFTER_EXPORT_ACTION,
        value=AfterExport.QUIT.value,
    )
    exp_nothing.grid(row=0, column=0, sticky='w')
    exp_minimise.grid(row=1, column=0, sticky='w')
    exp_quit.grid(row=2, column=0, sticky='w')

    add_tooltip(exp_nothing, _('After exports, do nothing and '
                               'keep the BEE2 in focus.'))
    add_tooltip(exp_minimise, _('After exports, minimise to the taskbar/dock.'))
    add_tooltip(exp_minimise, _('After exports, quit the BEE2.'))

    UI['launch_game'] = launch_game = make_checkbox(
        after_export_frame,
        section='General',
        item='launch_Game',
        var=LAUNCH_AFTER_EXPORT,
        desc=_('Launch Game'),
        tooltip=_('After exporting, launch the selected game automatically.'),
    )
    launch_game.grid(row=3, column=0, sticky='W', pady=(10, 0))

    if sound.initiallised:
        UI['mute'] = mute = make_checkbox(
            f,
            section='General',
            item='play_sounds',
            desc=_('Play Sounds'),
            var=PLAY_SOUND,
        )
    else:
        UI['mute'] = mute = ttk.Checkbutton(
            f,
            text=_('Play Sounds'),
            state='disabled',
        )
        add_tooltip(
            UI['mute'],
            _('Pyglet is either not installed or broken.\n'
              'Sound effects have been disabled.')
        )
    mute.grid(row=0, column=1, sticky='E')

    UI['reset_cache'] = reset_cache = ttk.Button(
        f,
        text=_('Reset Package Caches'),
        command=clear_caches,
    )
    reset_cache.grid(row=1, column=1, sticky='EW')
    add_tooltip(
        reset_cache,
        _('Force re-extracting all package resources. This requires a restart.'),
    )


def init_win_tab(f):
    UI['keep_inside'] = keep_inside = make_checkbox(
        f,
        section='General',
        item='keep_win_inside',
        desc=_('Keep windows inside screen'),
        tooltip=_('Prevent sub-windows from moving outside the screen borders. '
                  'If you have multiple monitors, disable this.'),
        var=KEEP_WIN_INSIDE,
    )
    keep_inside.grid(row=0, column=0, sticky=W)

    UI['reset_win'] = reset_win = ttk.Button(
        f,
        text=_('Reset All Window Positions'),
        # Indirect reference to allow UI to set this later
        command=lambda: reset_all_win(),
    )
    reset_win.grid(row=1, column=0, sticky=EW)


def init_dev_tab(f):
    f.columnconfigure(1, weight=1)
    f.columnconfigure(2, weight=1)

    make_checkbox(
        f,
        section='Debug',
        item='log_missing_ent_count',
        desc=_('Log missing entity counts'),
        tooltip=_('When loading items, log items with missing entity counts '
                  'in their properties.txt file.'),
    ).grid(row=0, column=0, sticky=W)

    make_checkbox(
        f,
        section='Debug',
        item='log_missing_styles',
        desc=_("Log when item doesn't have a style"),
        tooltip=_('Log items have no applicable version for a particular style.'
                  'This usually means it will look very bad.'),
    ).grid(row=1, column=0, sticky=W)

    make_checkbox(
        f,
        section='Debug',
        item='log_item_fallbacks',
        desc=_("Log when item uses parent's style"),
        tooltip=_('Log when an item reuses a variant from a parent style '
                  '(1970s using 1950s items, for example). This is usually '
                  'fine, but may need to be fixed.'),
    ).grid(row=3, column=0, sticky=W)

    make_checkbox(
        f,
        section='Debug',
        item='log_incorrect_packfile',
        desc=_("Log missing packfile resources"),
        tooltip=_('Log when the resources a "PackList" refers to are not '
                  'present in the zip. This may be fine (in a prerequisite zip),'
                  ' but it often indicates an error.'),
    ).grid(row=4, column=0, sticky=W)

    make_checkbox(
        f,
        section='General',
        item='preserve_bee2_resource_dir',
        desc=_('Preserve Game Directories'),
        tooltip=_('When exporting, do not overwrite \n"bee2/" and'
                  '\n"sdk_content/maps/bee2/".\n'
                  "Enable if you're"
                  ' developing new content, to ensure it is not '
                  'overwritten.'),
    ).grid(row=0, column=1, sticky=W)

    make_checkbox(
        f,
        section='Debug',
        item='show_log_win',
        desc=_('Show Log Window'),
        var=SHOW_LOG_WIN,
        tooltip=_('Show the log file in real-time.'),
    ).grid(row=1, column=1, sticky=W)
