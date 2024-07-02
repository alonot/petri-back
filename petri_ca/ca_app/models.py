from django.db import models
import uuid

class CAUser(models.Model):
    user_id = models.CharField(max_length=100, unique=True)
    random_string = models.CharField(max_length=100, unique=True, blank=True)

    def generate_random_string(self):
        # Generate a unique random string
        random_str = uuid.uuid4().hex

        # Ensure the random string is unique
        while CAUser.objects.filter(random_string=random_str).exists():
            random_str = uuid.uuid4().hex

        return random_str

    def save(self, *args, **kwargs):      #This will genereate teh random string if the strign is not genereatefd just to verify that the string is generated 
        # If the random string is not set, generate one
        if not self.random_string:
            self.random_string = self.generate_random_string()
        super().save(*args, **kwargs)
