def extract_name_and_enrollment(backend, user, response, *args, **kwargs):
    from accounts.models import StudentProfile

    profile, _ = StudentProfile.objects.get_or_create(user=user)

    # Example: "0901AM231031 Kavya Jain"
    full_name = response.get('name', '').strip()

    # Extract enrollment number and name from full_name
    if ' ' in full_name:
        enrollment, name = full_name.split(' ', 1)
    else:
        enrollment = ''
        name = full_name

    # Optional: Extract Google profile photo
    photo_url = response.get('picture', '')

    profile.enrollment_number = enrollment
    profile.name = name
    profile.photo_url = photo_url
    profile.save()
