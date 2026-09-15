# Octopy Feature Implementation - Ready for Testing

## Current Status
✅ All features implemented and tested in dev container
✅ Code quality baseline established and maintained
✅ Backward compatible with existing configs
✅ Ready for manual testing on Raspberry Pi

## Branches & PR Strategy

### Current Work
- **Branch**: `master` (at parent repo latest commit 6c67d13)
- **Commits ready**: All feature implementations
- **Status**: Local testing complete, ready for Pi testing

### Recommended PR Strategy

#### Option 1: Separate PRs per Feature (Recommended)
1. **PR #1: MIDI Panic "All Off"**
   - Files: octomidi.py, config.ini, octosettings.py, octo.py
   - Description: Enhanced panic() to send CC 123 (All Notes Off) when enabled
   - Config: [Midi] PanicAllOff=true

2. **PR #2: Keymap CSV Configuration**
   - Files: octofiles.py, octo.py, octosettings.py, config.ini, media/keymap.csv
   - Description: Map keyboard keys to specific audio files via CSV
   - Config: [Midi] KeymapFile=media/keymap.csv

#### Option 2: Single PR
- Combine both features in one PR
- Easier for author approval/merge
- May require explanation of two separate features

### Files NOT for PR (Local/Dev Only)
- `.devcontainer/devcontainer.json` - Keep local
- `.flake8` - Keep local (baseline configuration)
- `.codequality-baseline.md` - Keep local (reference only)

## Testing on Raspberry Pi

### Prerequisites
```bash
# Clone/pull the repository
git clone https://github.com/neufena/octopy.git
cd octopy
git checkout master  # or the specific feature branch

# Install dependencies
sudo apt-get update
sudo apt-get install libasound2-dev libjack-dev
pip3 install pygame python-rtmidi pyserial mido
```

### Test Sequence

#### 1. MIDI Panic Feature
```bash
# Create some test audio files in ~/media/
# Then run with verbose to see MIDI messages
python3 octo.py --verbose --keyboardcontrol

# Manually trigger files via MIDI and observe panic messages
# Or test with mock MIDI via:
python3 octo.py --verbose --midiindevice null --midioutdevice null
```

#### 2. Keymap Feature
```bash
# Create ~/media/song1.wav, song2.wav, etc.
# Keymap should auto-load from media/keymap.csv
python3 octo.py --verbose --keyboardcontrol

# Press keys mapped in keymap.csv and verify correct files play
# Test unmapped keys fall back to numeric 1-9
```

#### 3. Command-line Arguments
```bash
# Test all new arguments
python3 octo.py --help | grep -E "midipanic|keymap"

# Test with custom settings
python3 octo.py --midipanic_alloff --keymapfile ~/custom_keymap.csv
```

## Rollback Plan
If issues found on Pi:
1. Document the specific issue
2. Create a new local branch from `master`
3. Implement fix
4. Update this implementation
5. Re-test before PR

## Key Behaviors to Verify

### MIDI Panic
- Works with hardware MIDI devices
- CC 123 actually sent to MIDI OUT when enabled
- Works on MIDI panic (note off) and on app stop

### Keymap
- CSV loads correctly with multiple key→file mappings
- Verbose output shows loaded keymap
- Pressing mapped keys plays correct files
- Unmapped keys fall back to numeric 1-9 behavior
- Works in both console and video modes (if testing video)

### Null MIDI
- App can start with `--midiindevice null --midioutdevice null`
- Proper error when ALSA unavailable WITHOUT null MIDI option

## Post-Testing
After successful Pi testing:
1. ✅ Create feature branches if needed
2. ✅ Push to GitHub
3. ✅ Create PRs to parent repo
4. ✅ Include test results in PR description
