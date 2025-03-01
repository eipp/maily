import React, { useState, useCallback, useEffect } from 'react';
import { Button } from 'packages/ui/src/Button';
import { Avatar } from 'packages/ui/src/Avatar';
import { TextInput } from 'packages/ui/src/TextInput';
import { SelectInput } from 'packages/ui/src/SelectInput';
import { Card } from 'packages/ui/src/Card';
import { useToast } from 'apps/web/hooks/useToast';
import { useUserPermissions } from 'apps/web/hooks/useUserPermissions';

// Types
export interface Profile {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarUrl: string | null;
  department?: string;
  joinDate?: string;
}

export interface ProfileCardProps {
  profile?: Profile;
  isLoading?: boolean;
  defaultEditing?: boolean;
  allowEditing?: boolean;
  onSave?: (profile: Profile) => Promise<void>;
  onCancel?: () => void;
}

/**
 * ProfileCard component for displaying and editing user profiles
 */
export function ProfileCard({
  profile,
  isLoading = false,
  defaultEditing = false,
  allowEditing = true,
  onSave,
  onCancel
}: ProfileCardProps) {
  // State
  const [isEditing, setIsEditing] = useState(defaultEditing);
  const [editedProfile, setEditedProfile] = useState<Profile | undefined>(profile);
  const [isSaving, setIsSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Hooks
  const { showToast } = useToast();
  const { canEditUserProfile } = useUserPermissions();

  // Update local state when profile prop changes
  useEffect(() => {
    setEditedProfile(profile);
  }, [profile]);

  // Handle starting edit mode
  const handleEdit = useCallback(() => {
    setIsEditing(true);
    setEditedProfile(profile);
    setErrors({});
  }, [profile]);

  // Handle cancelling edit mode
  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setEditedProfile(profile);
    setErrors({});
    if (onCancel) {
      onCancel();
    }
  }, [profile, onCancel]);

  // Handle field changes in edit mode
  const handleChange = useCallback((field: keyof Profile, value: string) => {
    setEditedProfile(prev => {
      if (!prev) return prev;
      return { ...prev, [field]: value };
    });

    // Clear error for this field if it exists
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  }, [errors]);

  // Validate form fields
  const validateForm = useCallback(() => {
    const newErrors: Record<string, string> = {};

    if (!editedProfile?.name) {
      newErrors.name = 'Name is required';
    }

    if (!editedProfile?.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editedProfile.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!editedProfile?.role) {
      newErrors.role = 'Role is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [editedProfile]);

  // Handle saving changes
  const handleSave = useCallback(async () => {
    if (!validateForm() || !editedProfile) return;

    try {
      setIsSaving(true);

      if (onSave) {
        await onSave(editedProfile);
      }

      setIsEditing(false);
      showToast('Profile updated successfully', 'success');
    } catch (error) {
      console.error('Error saving profile:', error);
      showToast('Failed to update profile', 'error');
    } finally {
      setIsSaving(false);
    }
  }, [editedProfile, onSave, validateForm, showToast]);

  // Loading state
  if (isLoading) {
    return (
      <Card className="w-full max-w-md p-4 animate-pulse">
        <div className="flex items-center space-x-4">
          <div className="rounded-full bg-gray-200 h-16 w-16"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
        <div className="space-y-2 mt-4">
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </Card>
    );
  }

  // No profile provided
  if (!profile) {
    return (
      <Card className="w-full max-w-md p-4">
        <p className="text-gray-500 text-center">No profile information available</p>
      </Card>
    );
  }

  // Edit mode
  if (isEditing) {
    return (
      <Card className="w-full max-w-md p-4">
        <div className="space-y-4">
          <div className="flex justify-center">
            <Avatar
              src={editedProfile?.avatarUrl || undefined}
              name={editedProfile?.name || ''}
              size="lg"
            />
          </div>

          <TextInput
            label="Name"
            id="profile-name"
            value={editedProfile?.name || ''}
            onChange={(e) => handleChange('name', e.target.value)}
            error={errors.name}
          />

          <TextInput
            label="Email"
            id="profile-email"
            type="email"
            value={editedProfile?.email || ''}
            onChange={(e) => handleChange('email', e.target.value)}
            error={errors.email}
          />

          <SelectInput
            label="Role"
            id="profile-role"
            value={editedProfile?.role || ''}
            onChange={(e) => handleChange('role', e.target.value)}
            error={errors.role}
            options={[
              { value: 'Admin', label: 'Administrator' },
              { value: 'Editor', label: 'Editor' },
              { value: 'User', label: 'Standard User' },
              { value: 'Viewer', label: 'Viewer' },
            ]}
          />

          <SelectInput
            label="Department"
            id="profile-department"
            value={editedProfile?.department || ''}
            onChange={(e) => handleChange('department', e.target.value)}
            options={[
              { value: 'Engineering', label: 'Engineering' },
              { value: 'Marketing', label: 'Marketing' },
              { value: 'Sales', label: 'Sales' },
              { value: 'Support', label: 'Support' },
              { value: 'Content', label: 'Content' },
            ]}
          />

          <div className="flex justify-end space-x-2 mt-6">
            <Button
              variant="outline"
              onClick={handleCancel}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              loading={isSaving}
              disabled={isSaving}
            >
              Save Changes
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  // View mode
  return (
    <Card className="w-full max-w-md p-4">
      <div className="flex items-start">
        <Avatar
          src={profile.avatarUrl || undefined}
          name={profile.name}
          size="lg"
          className="mr-4"
        />

        <div className="flex-1">
          <h3 className="text-xl font-semibold">{profile.name}</h3>
          <p className="text-gray-600">{profile.email}</p>
          <div className="mt-2">
            <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
              {profile.role}
            </span>
            {profile.department && (
              <span className="inline-block ml-2 px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                {profile.department}
              </span>
            )}
          </div>

          {profile.joinDate && (
            <p className="text-sm text-gray-500 mt-2">
              Member since {new Date(profile.joinDate).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>

      {allowEditing && canEditUserProfile(profile.id) && (
        <div className="mt-4 text-right">
          <Button
            variant="outline"
            size="sm"
            onClick={handleEdit}
          >
            Edit Profile
          </Button>
        </div>
      )}
    </Card>
  );
}
