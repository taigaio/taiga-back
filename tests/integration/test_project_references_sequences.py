import pytest

from django.core import management
from django.conf import settings

from .. import factories


@pytest.fixture
def seq():
    from taiga.projects.references import sequences as seq
    return seq

@pytest.fixture
def refmodels():
    from taiga.projects.references import models
    return models

@pytest.mark.django_db
def test_sequences(seq):
    seqname = "foo"
    assert not seq.exists(seqname)

    # Create and check values
    seq.create(seqname)
    assert seq.exists(seqname)
    assert seq.next_value(seqname) == 1
    assert seq.next_value(seqname) == 2

    # Delete sequence
    seq.delete(seqname)
    assert not seq.exists(seqname)

    # Create new seq with same name
    # after previously deleted it
    seq.create(seqname)
    assert seq.next_value(seqname) == 1

    # Alter sequence
    seq.alter(seqname, 4)
    assert seq.next_value(seqname) == 5

    # Delete after alter
    seq.delete(seqname)
    assert not seq.exists(seqname)


@pytest.mark.django_db
def test_unique_reference_per_project(seq, refmodels):
    # management.call_command("loaddata", "initial_project_templates")
    domain = factories.DomainFactory(public_register=True)
    settings.DOMAIN_ID = domain.id

    project = factories.ProjectFactory.create()
    seqname = refmodels.make_sequence_name(project)

    assert seqname == "references_project1"
    assert seq.exists(seqname)

    assert refmodels.make_unique_reference_id(project, create=True) == 1
    assert refmodels.make_unique_reference_id(project, create=True) == 2

    project.delete()
    assert not seq.exists(seqname)
