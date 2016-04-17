"""
Distribution script for the RFID to MQTT bridge.
"""

import setuptools

setuptools.setup(

    # Package identity
    name="rfidreader",
    description="RFID reader client for the SL030 and Raspberry Pi",
    version="0.1",
    packages=["rfidreader", "rfidreader.commands"],

    # Package metadata
    author="Brett Lempereur",
    author_email="b.lempereur@outlook.com",
    license="MIT",
    url="https://github.com/brett-lempereur/rfidreader",

    # Dependencies
    install_requires=[
        "paho-mqtt>=1.1"
    ],

    # Console scripts
    entry_points={
        "console_scripts": [
            "rfid-bridge = rfidreader.commands.bridge:main"
        ]
    }

)
