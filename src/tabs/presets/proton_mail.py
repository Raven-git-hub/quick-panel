PRESET = {
    'label':     'Proton Mail',
    'preset_id': 'proton_mail',
    'type':      'web',
    'url':       'https://mail.proton.me',
    'icon':      'mail-unread-symbolic',
}
# Compatibility settings for proton.me (Safari user agent, on-demand
# hardware acceleration, Web Inspector) are applied automatically by the
# domain table in tabs/web_tab.py — they don't need to live in the tab
# config, so existing Proton tabs get them too.
