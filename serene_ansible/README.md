# serene_ansible

This repo contains ansible scripts to setup the following:

* jenkins and a `config.xml` files for each job in Jenkins which build serene projects, or run serene jobs. (see jenkins.yml)
* solr - including rack aware solr cloud setup and shard partitioning to match (see solr.yml)
* normalize.yml - helper to setup additional packages on your cluster that your serene jobs require

### Jenkins Dependencies

Jenkins requires a few plugins to be able to run these build jobs in entirety.

Major dependencies used are:

* git
* cobertura
* violations

Jenkins also requires connectivity to pypi repos which contain both the open source pypi mirror and internal mirror.  Both of these files are required:

```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = http://{{ YOUR INTERNAL REPO }}/sw/pypi/simple
extra-index-url = http://{{ YOUR INTERNAL REPO }}/sw/pypi/internal
trusted-host = {{ YOUR INTERNAL REPO }}
disable-pip-version-check = True
EOF
```

```bash
cat > ~/.pydistutils.cfg << EOF
[easy_install]
index-url = http://{{ YOUR_INTERNAL_REPO }}/sw/pypi/simple/
find-links = http://{{ YOUR_INTERNAL_REPO }}/sw/pypi/simple/
EOF
```

## jenkins python builds

The python build jobs are configured to:

1. pull from gitlab when it announces a push with a webhook
2. create a new python virtualenv
3. install/upgrade core python dependencies
4. install contents of repo
5. run tests and coverage reports
6. build source_distributable (.tar.gz)
7. deploy source_distributable to pypi repo

## jenkins job runners

Each of the job runners have build parameters which are requested when building. The builds are then configured to:

1. create a new python virtualenv
2. install/upgrade core python dependencies
3. install `serene_platform`
4. clone current admin repos
5. run a command from `serene_platform`
6. commit changes to admin repos


## TO update

You should make changes here and then use `ansible-playbook` to deploy them to your jenkins/solr/cdh cluster
