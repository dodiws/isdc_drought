from django.db import models


class HistoryDrought(models.Model):
    id = models.IntegerField(primary_key=True)
    ogc_fid = models.IntegerField(blank=True, null=True)
    min = models.FloatField(blank=True, null=True)
    mean = models.FloatField(blank=True, null=True)
    max = models.FloatField(blank=True, null=True)
    std = models.FloatField(blank=True, null=True)
    sum = models.FloatField(blank=True, null=True)
    count = models.FloatField(blank=True, null=True)
    basin_id = models.FloatField(blank=True, null=True)
    agg_code = models.CharField(max_length=50, blank=True)
    woy = models.CharField(max_length=50, blank=True)
    class Meta:
        managed = True
        db_table = 'history_drought'
