from setuptools import setup
import os
from glob import glob

package_name = 'lost_item_detector'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ssafy',
    maintainer_email='onono1141@gmail.com',
    description='분실물 감지 노드',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detector_node = lost_item_detector.detector_node:main',
            'detector_node_mock = lost_item_detector.detector_node_mock:main',
            'trigger_node = lost_item_detector.trigger_node:main',
        ],
    },
)
