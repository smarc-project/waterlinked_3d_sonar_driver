from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'wl_3dsonar_driver'

setup(
    name=package_name,
    version='0.0.0',
    #packages=find_packages(include=['wl_3dsonar_driver', 'wl_api'], exclude=['test']),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    #package_dir={
    #    'wl_3dsonar_driver': 'wl_3dsonar_driver',
    #    'wl_api': 'wl_api',
    #},
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('src/launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='babypool',
    maintainer_email='you@example.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'wl_3dsonar_driver_node = wl_3dsonar_driver.sonar_3d_15_node:main',
        ],
    },
)
