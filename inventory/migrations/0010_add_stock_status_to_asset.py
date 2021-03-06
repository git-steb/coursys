# Generated by Django 2.2.4 on 2019-09-10 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_add_fields_to_assets'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='stock_status',
            field=models.DecimalField(blank=True, choices=[(2, 'In Stock'), (3, 'Unknown'), (0, 'Out of stock'), (1, 'Low Stock')], decimal_places=0, max_digits=1, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='category',
            field=models.CharField(blank=True, choices=[('BROC', 'Brochures'), ('GEN', 'General'), ('ADMN', 'Admin Support'), ('TECH', 'Tech Support'), ('EVEN', 'Events'), ('OFF', 'Office Supplies'), ('SWAG', 'Swag'), ('RESR', 'Research'), ('ELEC', 'Electronics'), ('TEAC', 'Teaching')], default='GEN', max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='in_use',
            field=models.BooleanField(default=False, verbose_name='Currently in Use'),
        ),
    ]
