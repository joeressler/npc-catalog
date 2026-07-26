from django.db import models


class Campaign(models.Model):
    name = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to="campaigns/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class NPC(models.Model):
    ALIGNMENT_CHOICES = [
        ("LG", "Lawful Good"),
        ("NG", "Neutral Good"),
        ("CG", "Chaotic Good"),
        ("LN", "Lawful Neutral"),
        ("N", "True Neutral"),
        ("CN", "Chaotic Neutral"),
        ("LE", "Lawful Evil"),
        ("NE", "Neutral Evil"),
        ("CE", "Chaotic Evil"),
    ]

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="npcs",
    )
    name = models.CharField(max_length=200)
    role_occupation = models.CharField(max_length=200)
    alignment = models.CharField(max_length=2, choices=ALIGNMENT_CHOICES)
    location = models.CharField(max_length=200)
    faction = models.CharField(max_length=200, blank=True)
    attitude = models.CharField(max_length=200)
    party_relationship = models.CharField(max_length=200)
    appearance = models.TextField(blank=True)
    voice_mannerisms = models.TextField(blank=True)
    personality_traits = models.TextField(blank=True)
    motivation_goal = models.TextField(blank=True)
    secret_hook = models.TextField(blank=True)
    knowledge = models.TextField(blank=True)
    inventory = models.TextField(blank=True)
    dm_notes = models.TextField(blank=True)
    session_log = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="npcs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["campaign", "name"]),
            models.Index(fields=["alignment"]),
            models.Index(fields=["location"]),
            models.Index(fields=["faction"]),
        ]

    def __str__(self):
        return self.name


class Alias(models.Model):
    npc = models.ForeignKey(
        NPC,
        on_delete=models.CASCADE,
        related_name="aliases",
    )
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        unique_together = [["npc", "name"]]

    def __str__(self):
        return self.name
