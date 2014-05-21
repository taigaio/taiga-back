import pytest

@pytest.fixture
def seq():
    from taiga.projects.references import sequences as seq
    return seq

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
