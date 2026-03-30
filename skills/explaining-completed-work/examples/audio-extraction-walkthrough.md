# Example: Audio Extraction Walkthrough

## Scenario

The user asked to extract the audio from two `.mp4` files, preserve the original audio quality as much as possible, and add the result to the macOS Music app.

## Example Explanation

### Result

I extracted the audio tracks from both videos into standalone `.m4a` files and imported those files into the Music app.

### Mechanism

An `.mp4` file is a container. It can hold a video stream and an audio stream at the same time. I first checked the source audio codec and found that both files already contained AAC audio. Because of that, I did not re-encode the audio. I copied the audio stream out directly into `.m4a`, then used AppleScript to tell the Music app to add those files to the library.

### Reason

Re-encoding AAC audio would only create a second lossy compression step. Copying the stream preserved the exact audio that was already inside the video file. That was the safest way to keep the best available quality from the source.

### Concept

Think of the `.mp4` file as a box with two items inside: a video track and an audio track. Extracting audio does not mean "turning pictures into sound." It means opening the box and taking the audio item out separately.

The deeper version is that the container and the codec are different things:

- container: the file wrapper, such as `.mp4`
- codec: the encoding method for the audio or video inside, such as AAC or H.264

### Boundary

This preserved the original AAC track without adding another compression pass, but it did not turn an already lossy source into true lossless audio. "No extra loss" and "source is lossless" are different claims.
