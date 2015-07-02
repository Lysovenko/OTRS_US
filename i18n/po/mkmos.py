from imp import find_module, load_module
import os

pth = os.path.join(os.path.split(os.__file__)[0], 'Tools', 'i18n')
try:
    fptr, pth, dsc = find_module('msgfmt', [pth])
except ImportError:
    print('ImportError: %s' % pth)
    exit()
msgfmt = load_module('msgfmt', fptr, pth, dsc)
del fptr, pth, dsc

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
