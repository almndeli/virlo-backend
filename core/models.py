from django.db import models

class Trend(models.Model):
    PLATFORM_TIKTOK = "tiktok"
    PLATFORM_INSTAGRAM = "instagram"
    PLATFORM_YOUTUBE = "youtube"

    PLATFORM_CHOICES = [
        (PLATFORM_TIKTOK, "TikTok"),
        (PLATFORM_INSTAGRAM, "Instagram"),
        (PLATFORM_YOUTUBE, "YouTube"),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    keyword = models.CharField(max_length=255)
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform}: {self.keyword} ({self.score})"
