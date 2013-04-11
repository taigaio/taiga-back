
============
Coding rules
============

Django models
=============

* All model names in singular an CamelCase.

* All models have a **Meta** with at least:

  - **verbose_name** and **verbose_name_plural**: unicode strings, lowercase, with spaces.
  - **ordering**: return a consistent order, using pk if no other unique field or combination exists.

* All models have **__unicode__** method, returning a human-readable, descriptive, short text.

* All fields have **verbose_name**. Also **help_text** if needed to fully explain the field meaning.

* All fields have explicit **blank** and **null** parameters. Use only those combinations, unless
  there a documented need of other thing:

  Normal fields (IntegerField, DateField, ForeignKey, FileField...)
    - (optional) **null = True**, **blank = True**
    - (required) **null = False**, **blank = False**

  Text fields (CharField, TextField, URLField...)
    - (optional) **null = False**, **blank = True**
    - (required) **null = False**, **blank = False**

  Boolean fields:
    - (two values, T/F) **null = False**, **blank = True**
    - (three values, T/F/Null) **null = False**, **blank = True**

* Don't create text fields with **null = True**, unless you need to distinguish between empty string and None.

* Don't create boolean fields with **blank = False**, otherwise they could only be True.

Example::

    class SomeClass(models.Model):
        name = models.CharField(max_length=100, null = False, blank = False, unique=True,
                   verbose_name = _(u'name'))
        slug = models.SlugField(max_length=100, null = False, blank = False, unique=True,
                   verbose_name = _(u'slug'),
                   help_text = (u'Identifier of this object. Only letters, digits and underscore "_" allowed.'))
        text = models.TextField(null = False, blank = True,
                   verbose_name = _(u'text'))

        class Meta:
            verbose_name = _(u'some class')
            verbose_name_plural = _(u'some classes')
            ordering = ['name']

        def __unicode__(self):
            return self.name

