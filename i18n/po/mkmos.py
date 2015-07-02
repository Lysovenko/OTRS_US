import os
try:
    import Tools.i18n.msgfmt as msgfmt
except ImportError:
    print('ImportError: can not import Tools.i18n.msgfmt')
    exit()


if __name__ == '__main__':
    # Ensure that we are in the "po" directory
    os.chdir(os.path.dirname(__file__))
    po_files = [ i for i in os.listdir('.') if i.endswith('.po')]
    for po in po_files:
        print (po[:-3])
        mo_dir = os.path.join("..", "locale", po[:-3], "LC_MESSAGES")
        if not os.path.isdir(mo_dir):
            os.makedirs(mo_dir)
        msgfmt.make(po, os.path.join(mo_dir, "otrs_us.mo"))
