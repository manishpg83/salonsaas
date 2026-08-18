from apps.core.models import SalonScopedModel, TimeStampedModel


def test_timestamped_model_is_abstract_with_expected_fields():
    assert TimeStampedModel._meta.abstract is True
    field_names = {f.name for f in TimeStampedModel._meta.get_fields()}
    assert {"created_at", "updated_at"} <= field_names


def test_salon_scoped_model_is_abstract_and_adds_salon_fk():
    assert SalonScopedModel._meta.abstract is True
    field_names = {f.name for f in SalonScopedModel._meta.get_fields()}
    assert {"created_at", "updated_at", "salon"} <= field_names

    salon_field = SalonScopedModel._meta.get_field("salon")
    assert salon_field.many_to_one is True
    assert salon_field.remote_field.on_delete.__name__ == "CASCADE"
    assert salon_field.remote_field.related_name == "+"
