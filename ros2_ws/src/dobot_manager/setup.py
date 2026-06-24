from setuptools import find_packages, setup

package_name = 'dobot_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pymodbus==2.5.3'],
    zip_safe=True,
    maintainer='ssafy',
    maintainer_email='tanyatws15@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'task_manager = dobot_manager.dobot_task_manager:main',
        ],
    },
)
