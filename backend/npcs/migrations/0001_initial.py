from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
                ("image", models.ImageField(blank=True, null=True, upload_to="campaigns/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="NPC",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("role_occupation", models.CharField(max_length=200)),
                (
                    "alignment",
                    models.CharField(
                        choices=[
                            ("LG", "Lawful Good"),
                            ("NG", "Neutral Good"),
                            ("CG", "Chaotic Good"),
                            ("LN", "Lawful Neutral"),
                            ("N", "True Neutral"),
                            ("CN", "Chaotic Neutral"),
                            ("LE", "Lawful Evil"),
                            ("NE", "Neutral Evil"),
                            ("CE", "Chaotic Evil"),
                        ],
                        max_length=2,
                    ),
                ),
                ("location", models.CharField(max_length=200)),
                ("faction", models.CharField(blank=True, max_length=200)),
                ("attitude", models.CharField(max_length=200)),
                ("party_relationship", models.CharField(max_length=200)),
                ("appearance", models.TextField(blank=True)),
                ("voice_mannerisms", models.TextField(blank=True)),
                ("personality_traits", models.TextField(blank=True)),
                ("motivation_goal", models.TextField(blank=True)),
                ("secret_hook", models.TextField(blank=True)),
                ("knowledge", models.TextField(blank=True)),
                ("inventory", models.TextField(blank=True)),
                ("dm_notes", models.TextField(blank=True)),
                ("session_log", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="npcs",
                        to="npcs.campaign",
                    ),
                ),
                ("tags", models.ManyToManyField(blank=True, related_name="npcs", to="npcs.tag")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Alias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                (
                    "npc",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="aliases",
                        to="npcs.npc",
                    ),
                ),
            ],
            options={"ordering": ["name"], "unique_together": {("npc", "name")}},
        ),
        migrations.AddIndex(
            model_name="npc",
            index=models.Index(fields=["campaign", "name"], name="npcs_npc_campaig_8f0f0a_idx"),
        ),
        migrations.AddIndex(
            model_name="npc",
            index=models.Index(fields=["alignment"], name="npcs_npc_alignme_6e8f0a_idx"),
        ),
        migrations.AddIndex(
            model_name="npc",
            index=models.Index(fields=["location"], name="npcs_npc_locatio_7e8f0a_idx"),
        ),
        migrations.AddIndex(
            model_name="npc",
            index=models.Index(fields=["faction"], name="npcs_npc_faction_8e8f0a_idx"),
        ),
    ]
