SIDEBAR_BUTTON_STYLE = ('''
    QPushButton{
    border: none;
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 500;
    color: #8E8E93;
    background: transparent;
    text-align: left;
    border-radius: 8px;
    margin: 0px;
    }
    QPushButton:hover {
    background: #E5E5EA;
    }
    QPushButton:pressed {
        background: #D1D1D6;
    }
    QPushButton[active="true"] {
        background: #D1D1D6;
        color: black;
        font-weight: 600;
    }
''')

ROUNDED_MENU_STYLE = """
QMenu {
    background-color: rgba(245, 245, 247, 250);
    border: 1px solid rgba(180, 182, 190, 210);
    border-radius: 10px;
    padding: 5px;
}
QMenu::item {
    padding: 6px 20px 6px 16px;
    border-radius: 6px;
    color: #202124;
    font-size: 13px;
}
QMenu::item:selected {
    background: #1684FC;
    color: #FFFFFF;
}
QMenu::item:disabled {
    color: #8E8E93;
}
QMenu::separator {
    height: 1px;
    background: rgba(0, 0, 0, 0.10);
    margin: 4px 8px;
}
"""