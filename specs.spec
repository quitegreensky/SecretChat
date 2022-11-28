# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import os


'''
packages which will be included to final dist
'''
datas = []

current_path = os.getcwd()
a = Analysis(['client.py'],
             pathex=[current_path],
             binaries=[],
             datas=datas,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
	  [],
          name='SecretChat',
          debug=False,
          strip=False,
          upx=True,
          console=True )


app = BUNDLE(exe,
             name='SecretChat',
             bundle_identifier=None)