import os

from conjureup.app_config import app
from conjureup.bundlewriter import BundleWriter


def write_bundle(assignments):
    bundle = app.metadata_controller.bundle
    bw = BundleWriter(assignments, bundle)
    fn = os.path.join(app.config['spell-dir'],
                      'deployed-bundle.yaml')
    bw.write_bundle(fn)
