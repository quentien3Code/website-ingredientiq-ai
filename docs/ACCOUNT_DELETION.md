# Automatic Account Deletion System

This system handles automatic deletion of premium user accounts after a 30-day grace period.

## How It Works

### For Freemium Users
- Account is deleted **immediately** when they request deletion
- No grace period or cancellation option

### For Premium Users
- Account deletion is **scheduled for 30 days** in the future
- If user logs in during the 30-day period, deletion request is **automatically cancelled**
- After 30 days, account is **automatically deleted** by the system

## Management Commands

### 1. Delete Scheduled Accounts
```bash
# Delete accounts that are past their scheduled deletion date
python manage.py delete_scheduled_accounts

# Dry run (see what would be deleted without actually deleting)
python manage.py delete_scheduled_accounts --dry-run

# Force delete all pending deletion requests (use with caution)
python manage.py delete_scheduled_accounts --force
```

### 2. Check Deletion Requests
```bash
# Check all pending deletion requests
python manage.py check_deletion_requests

# Check requests scheduled for deletion in the next 7 days
python manage.py check_deletion_requests --days 7
```

## Setting Up Automatic Deletion

### Option 1: Cron Job (Recommended for Production)
```bash
# Run the setup script
./setup_account_deletion_cron.sh

# This will create a daily cron job that runs at 2:00 AM
# Logs are written to /var/log/account_deletion.log
```

### Option 2: Manual Setup
Add this line to your crontab:
```bash
0 2 * * * cd /path/to/your/project && python manage.py delete_scheduled_accounts >> /var/log/account_deletion.log 2>&1
```

### Option 3: Background Task (Celery)
If you're using Celery, you can create a periodic task:
```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def delete_scheduled_accounts():
    call_command('delete_scheduled_accounts')
```

## Database Models

### AccountDeletionRequest
- `user`: OneToOneField to User
- `requested_at`: When deletion was requested
- `scheduled_deletion_date`: When account should be deleted (30 days later)
- `status`: 'pending', 'cancelled', or 'completed'
- `cancelled_at`: When cancellation occurred (if applicable)

## API Endpoints

### DELETE /foodapp/user-profile/
- **Freemium users**: Immediate deletion
- **Premium users**: Schedule deletion for 30 days later

### POST /foodapp/login/
- Automatically cancels any pending deletion requests for premium users

## Monitoring

### Check Logs
```bash
# View deletion logs
tail -f /var/log/account_deletion.log

# Check cron job status
crontab -l
```

### Database Queries
```python
# Check pending deletions
from foodinfo.models import AccountDeletionRequest
pending = AccountDeletionRequest.objects.filter(status='pending')

# Check overdue deletions
from django.utils import timezone
overdue = pending.filter(scheduled_deletion_date__lte=timezone.now())
```

## Testing

### Test the Commands
```bash
# Test dry run
python manage.py delete_scheduled_accounts --dry-run

# Test status check
python manage.py check_deletion_requests

# Test with a specific user (create deletion request first)
python manage.py shell
>>> from foodinfo.models import AccountDeletionRequest, User
>>> user = User.objects.get(email='test@example.com')
>>> request = AccountDeletionRequest.objects.create(user=user, scheduled_deletion_date=timezone.now())
>>> # Then run the deletion command
```

## Security Considerations

1. **Logging**: All deletions are logged for audit purposes
2. **Grace Period**: 30-day delay prevents accidental deletions
3. **Cancellation**: Login automatically cancels deletion requests
4. **Dry Run**: Always test with `--dry-run` first
5. **Backup**: Ensure you have database backups before running deletions
6. **Foreign Key Constraints**: System safely handles all foreign key relationships during deletion

## Troubleshooting

### Common Issues

1. **Cron job not running**
   - Check crontab: `crontab -l`
   - Check logs: `tail -f /var/log/account_deletion.log`
   - Verify paths in cron job

2. **Permission errors**
   - Ensure Django user has write access to log directory
   - Check file permissions on manage.py

3. **Database errors**
   - Check database connectivity
   - Verify model relationships
   - Check for foreign key constraints
   - The system now safely handles foreign key constraints automatically

### Manual Cleanup
If you need to manually clean up:
```python
# Cancel all pending deletions
from foodinfo.models import AccountDeletionRequest
AccountDeletionRequest.objects.filter(status='pending').update(status='cancelled', cancelled_at=timezone.now())
```
