import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'fr3_wave'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gganjang',
    maintainer_email='junhjang@keti.re.kr',
    description='FR3 trajectory clients for a shared MuJoCo ros2_control simulator.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'wave = fr3_wave.wave:main',
            'spin = fr3_wave.spin:main',
        ],
    },
)
