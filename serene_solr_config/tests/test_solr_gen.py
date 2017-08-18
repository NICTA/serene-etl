from serene_solr_config.main import make_config
import shutil, os
import tempfile

# Todo - check XML validation of files generated...



def test_solr_generation():

    tmp = tempfile.mkdtemp()
    os.removedirs(tmp)

    make_config(
        _version='6.0.0',
        _config='data_driven_schema_configs',
        _output=tmp
    )

    shutil.rmtree(tmp)

