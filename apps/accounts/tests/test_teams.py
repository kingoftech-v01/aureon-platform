"""
Tests for Team, TeamMember, and TeamInvitation models and their ViewSets.

Tests cover:
- Team model creation, __str__, member_count property
- TeamMember model creation, __str__, unique_together constraint
- TeamInvitation model creation, __str__, is_expired, accept, cancel methods
- TeamViewSet CRUD + custom actions (members, invite, remove_member, stats)
- TeamMemberViewSet listing and permissions
- TeamInvitationViewSet CRUD + custom actions (cancel, accept)
"""

import pytest
import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User, Team, TeamMember, TeamInvitation


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def owner(db):
    """Create a team owner user."""
    return User.objects.create_user(
        username='teamowner',
        email='teamowner@test.com',
        password='SecurePass123!',
        first_name='Team',
        last_name='Owner',
        role=User.ADMIN,
        is_active=True,
    )


@pytest.fixture
def member_user(db):
    """Create a regular team member user."""
    return User.objects.create_user(
        username='member',
        email='member@test.com',
        password='SecurePass123!',
        first_name='Team',
        last_name='Member',
        role=User.CONTRIBUTOR,
        is_active=True,
    )


@pytest.fixture
def other_user(db):
    """Create another user not in any team."""
    return User.objects.create_user(
        username='otheruser',
        email='other@test.com',
        password='SecurePass123!',
        first_name='Other',
        last_name='User',
        role=User.CONTRIBUTOR,
        is_active=True,
    )


@pytest.fixture
def team(db, owner):
    """Create a team."""
    return Team.objects.create(
        name='Test Team',
        description='A test team',
        owner=owner,
        is_active=True,
    )


@pytest.fixture
def team_member_owner(db, team, owner):
    """Create the owner as a team member."""
    return TeamMember.objects.create(
        team=team,
        user=owner,
        role=TeamMember.OWNER,
    )


@pytest.fixture
def team_member(db, team, member_user):
    """Create a regular team member."""
    return TeamMember.objects.create(
        team=team,
        user=member_user,
        role=TeamMember.MEMBER,
    )


@pytest.fixture
def team_invitation(db, team, owner):
    """Create a team invitation."""
    return TeamInvitation.objects.create(
        team=team,
        email='invited@test.com',
        role=TeamMember.MEMBER,
        invited_by=owner,
        invitation_token=secrets.token_urlsafe(32),
        expires_at=timezone.now() + timedelta(days=7),
        status=TeamInvitation.PENDING,
    )


@pytest.fixture
def api_client():
    """Create an API client."""
    client = APIClient()
    client.defaults['HTTP_ORIGIN'] = 'http://testserver'
    client.defaults['SERVER_NAME'] = 'testserver'
    return client


@pytest.fixture
def owner_client(api_client, owner):
    """Create an authenticated API client for the owner."""
    api_client.force_authenticate(user=owner)
    return api_client


@pytest.fixture
def member_client(api_client, member_user):
    """Create an authenticated API client for a member."""
    api_client.force_authenticate(user=member_user)
    return api_client


# ============================================================================
# Team Model Tests
# ============================================================================

@pytest.mark.django_db
class TestTeamModel:
    """Tests for the Team model."""

    def test_create_team(self, team):
        """Test creating a team."""
        assert team.pk is not None
        assert team.name == 'Test Team'
        assert team.is_active is True

    def test_str_representation(self, team):
        """Test __str__ returns team name."""
        assert str(team) == 'Test Team'

    def test_member_count_with_no_members(self, team):
        """Test member_count returns 0 when no members."""
        assert team.member_count == 0

    def test_member_count_with_members(self, team, team_member_owner, team_member):
        """Test member_count returns correct count."""
        assert team.member_count == 2

    def test_team_default_ordering(self, owner):
        """Test teams are ordered by -created_at."""
        t1 = Team.objects.create(name='First Team', owner=owner)
        t2 = Team.objects.create(name='Second Team', owner=owner)
        teams = list(Team.objects.filter(owner=owner))
        assert teams[0] == t2
        assert teams[1] == t1

    def test_team_metadata_default(self, team):
        """Test metadata defaults to empty dict."""
        assert team.metadata == {}


# ============================================================================
# TeamMember Model Tests
# ============================================================================

@pytest.mark.django_db
class TestTeamMemberModel:
    """Tests for the TeamMember model."""

    def test_create_team_member(self, team_member):
        """Test creating a team member."""
        assert team_member.pk is not None
        assert team_member.role == TeamMember.MEMBER

    def test_str_representation(self, team_member, member_user, team):
        """Test __str__ returns user, team, and role."""
        expected = f"{member_user.get_full_name()} - {team.name} ({TeamMember.MEMBER})"
        assert str(team_member) == expected

    def test_unique_together_team_user(self, team, member_user, team_member):
        """Test that same user cannot be added to team twice."""
        with pytest.raises(Exception):
            TeamMember.objects.create(
                team=team,
                user=member_user,
                role=TeamMember.ADMIN,
            )

    def test_all_role_choices(self, team):
        """Test all role choices can be set."""
        for role_value, _ in TeamMember.ROLE_CHOICES:
            user = User.objects.create_user(
                username=f'role_{role_value}',
                email=f'role_{role_value}@test.com',
                password='SecurePass123!',
            )
            tm = TeamMember.objects.create(team=team, user=user, role=role_value)
            assert tm.role == role_value


# ============================================================================
# TeamInvitation Model Tests
# ============================================================================

@pytest.mark.django_db
class TestTeamInvitationModel:
    """Tests for the TeamInvitation model."""

    def test_create_invitation(self, team_invitation):
        """Test creating a team invitation."""
        assert team_invitation.pk is not None
        assert team_invitation.status == TeamInvitation.PENDING
        assert team_invitation.email == 'invited@test.com'

    def test_str_representation(self, team_invitation, team):
        """Test __str__ returns email, team name, and status."""
        expected = f"Team invite to invited@test.com for {team.name} (pending)"
        assert str(team_invitation) == expected

    def test_is_expired_when_future(self, team_invitation):
        """Test is_expired returns False when expires_at is in the future."""
        assert team_invitation.is_expired is False

    def test_is_expired_when_past(self, team, owner):
        """Test is_expired returns True when expires_at is in the past."""
        invitation = TeamInvitation.objects.create(
            team=team,
            email='expired@test.com',
            role=TeamMember.MEMBER,
            invited_by=owner,
            invitation_token=secrets.token_urlsafe(32),
            expires_at=timezone.now() - timedelta(hours=1),
            status=TeamInvitation.PENDING,
        )
        assert invitation.is_expired is True

    def test_is_expired_false_when_accepted(self, team, owner):
        """Test is_expired returns False when status is accepted."""
        invitation = TeamInvitation.objects.create(
            team=team,
            email='accepted@test.com',
            role=TeamMember.MEMBER,
            invited_by=owner,
            invitation_token=secrets.token_urlsafe(32),
            expires_at=timezone.now() - timedelta(hours=1),
            status=TeamInvitation.ACCEPTED,
        )
        assert invitation.is_expired is False

    def test_accept_invitation(self, team_invitation, other_user):
        """Test accepting a team invitation creates membership."""
        team_invitation.accept(other_user)

        team_invitation.refresh_from_db()
        assert team_invitation.status == TeamInvitation.ACCEPTED
        assert team_invitation.accepted_at is not None

        # Verify membership was created
        assert TeamMember.objects.filter(
            team=team_invitation.team,
            user=other_user,
        ).exists()

    def test_cancel_invitation(self, team_invitation):
        """Test cancelling a team invitation."""
        team_invitation.cancel()

        team_invitation.refresh_from_db()
        assert team_invitation.status == TeamInvitation.CANCELLED


# ============================================================================
# TeamViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestTeamViewSet:
    """Tests for the TeamViewSet."""

    def test_list_teams(self, owner_client, team, team_member_owner):
        """Test listing teams returns user's teams."""
        response = owner_client.get('/api/auth/api/teams/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Team'

    def test_create_team(self, owner_client, owner):
        """Test creating a new team."""
        data = {
            'name': 'New Team',
            'description': 'A brand new team',
        }
        response = owner_client.post('/api/auth/api/teams/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Team'

        # Verify owner membership was created
        new_team = Team.objects.get(name='New Team')
        assert TeamMember.objects.filter(
            team=new_team,
            user=owner,
            role=TeamMember.OWNER,
        ).exists()

    def test_retrieve_team_detail(self, owner_client, team, team_member_owner):
        """Test retrieving team detail includes members."""
        response = owner_client.get(f'/api/auth/api/teams/{team.pk}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Team'
        assert 'members' in response.data

    def test_update_team(self, owner_client, team, team_member_owner):
        """Test updating a team."""
        data = {'name': 'Updated Team Name', 'description': 'Updated description'}
        response = owner_client.put(f'/api/auth/api/teams/{team.pk}/', data)
        assert response.status_code == status.HTTP_200_OK

        team.refresh_from_db()
        assert team.name == 'Updated Team Name'

    def test_partial_update_team(self, owner_client, team, team_member_owner):
        """Test partially updating a team."""
        data = {'description': 'Only description changed'}
        response = owner_client.patch(f'/api/auth/api/teams/{team.pk}/', data)
        assert response.status_code == status.HTTP_200_OK

        team.refresh_from_db()
        assert team.description == 'Only description changed'

    def test_delete_team(self, owner_client, team, team_member_owner):
        """Test deleting a team."""
        response = owner_client.delete(f'/api/auth/api/teams/{team.pk}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Team.objects.filter(pk=team.pk).exists()

    def test_members_action(self, owner_client, team, team_member_owner, team_member):
        """Test listing team members via the members action."""
        response = owner_client.get(f'/api/auth/api/teams/{team.pk}/members/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_invite_action(self, owner_client, team, team_member_owner):
        """Test inviting a user to a team."""
        data = {'email': 'newinvite@test.com', 'role': TeamMember.MEMBER}
        response = owner_client.post(f'/api/auth/api/teams/{team.pk}/invite/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert TeamInvitation.objects.filter(
            team=team,
            email='newinvite@test.com',
        ).exists()

    def test_invite_action_missing_email(self, owner_client, team, team_member_owner):
        """Test invite action returns error when email is missing."""
        response = owner_client.post(f'/api/auth/api/teams/{team.pk}/invite/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_remove_member_action(self, owner_client, team, team_member_owner, team_member, member_user):
        """Test removing a member from the team."""
        data = {'user_id': str(member_user.pk)}
        response = owner_client.post(
            f'/api/auth/api/teams/{team.pk}/remove_member/', data
        )
        assert response.status_code == status.HTTP_200_OK
        assert not TeamMember.objects.filter(
            team=team, user=member_user
        ).exists()

    def test_remove_member_action_cannot_remove_owner(self, owner_client, team, team_member_owner, owner):
        """Test that the owner cannot be removed."""
        data = {'user_id': str(owner.pk)}
        response = owner_client.post(
            f'/api/auth/api/teams/{team.pk}/remove_member/', data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Cannot remove the team owner' in response.data['error']

    def test_remove_member_action_missing_user_id(self, owner_client, team, team_member_owner):
        """Test remove_member returns error when user_id is missing."""
        response = owner_client.post(
            f'/api/auth/api/teams/{team.pk}/remove_member/', {}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_member_action_nonexistent_member(self, owner_client, team, team_member_owner, other_user):
        """Test remove_member returns 404 for non-member."""
        data = {'user_id': str(other_user.pk)}
        response = owner_client.post(
            f'/api/auth/api/teams/{team.pk}/remove_member/', data
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_stats_action(self, owner_client, team, team_member_owner, team_member):
        """Test getting team statistics."""
        response = owner_client.get('/api/auth/api/teams/stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_teams' in response.data
        assert 'active_teams' in response.data
        assert 'total_members' in response.data

    def test_unauthenticated_list(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/auth/api/teams/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TeamMemberViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestTeamMemberViewSet:
    """Tests for the TeamMemberViewSet."""

    def test_list_team_members(self, owner_client, team_member_owner, team_member):
        """Test listing team members."""
        response = owner_client.get('/api/auth/api/team-members/')
        assert response.status_code == status.HTTP_200_OK
        # Owner should see members from teams they own
        assert len(response.data['results']) >= 1

    def test_member_sees_own_memberships(self, member_client, team_member):
        """Test that a member can see their own memberships."""
        response = member_client.get('/api/auth/api/team-members/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_unauthenticated_list(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/auth/api/team-members/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TeamInvitationViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestTeamInvitationViewSet:
    """Tests for the TeamInvitationViewSet."""

    def test_list_invitations(self, owner_client, team_invitation):
        """Test listing team invitations."""
        response = owner_client.get('/api/auth/api/team-invitations/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_retrieve_invitation(self, owner_client, team_invitation):
        """Test retrieving a single invitation."""
        response = owner_client.get(
            f'/api/auth/api/team-invitations/{team_invitation.pk}/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'invited@test.com'

    def test_cancel_invitation(self, owner_client, team_invitation):
        """Test cancelling an invitation."""
        response = owner_client.post(
            f'/api/auth/api/team-invitations/{team_invitation.pk}/cancel/'
        )
        assert response.status_code == status.HTTP_200_OK

        team_invitation.refresh_from_db()
        assert team_invitation.status == TeamInvitation.CANCELLED

    def test_accept_invitation(self, owner_client, team_invitation, owner):
        """Test accepting a team invitation via token."""
        data = {'token': team_invitation.invitation_token}
        response = owner_client.post('/api/auth/api/team-invitations/accept/', data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['role'] == team_invitation.role

        team_invitation.refresh_from_db()
        assert team_invitation.status == TeamInvitation.ACCEPTED

    def test_accept_invitation_missing_token(self, owner_client):
        """Test accept returns error when token is missing."""
        response = owner_client.post('/api/auth/api/team-invitations/accept/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_invitation_invalid_token(self, owner_client):
        """Test accept returns 404 for invalid token."""
        data = {'token': 'invalid-token-value'}
        response = owner_client.post('/api/auth/api/team-invitations/accept/', data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_accept_expired_invitation(self, owner_client, team, owner):
        """Test accept returns error for expired invitation."""
        invitation = TeamInvitation.objects.create(
            team=team,
            email='expired@test.com',
            role=TeamMember.MEMBER,
            invited_by=owner,
            invitation_token=secrets.token_urlsafe(32),
            expires_at=timezone.now() - timedelta(hours=1),
            status=TeamInvitation.PENDING,
        )
        data = {'token': invitation.invitation_token}
        response = owner_client.post('/api/auth/api/team-invitations/accept/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        invitation.refresh_from_db()
        assert invitation.status == TeamInvitation.EXPIRED

    def test_unauthenticated_list(self, api_client):
        """Test that unauthenticated requests are rejected."""
        response = api_client.get('/api/auth/api/team-invitations/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
