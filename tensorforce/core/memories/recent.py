# Copyright 2018 Tensorforce Team. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import tensorflow as tf

from tensorforce import util
from tensorforce.core.memories import Queue


class Recent(Queue):
    """
    Batching memory which always retrieves most recent experiences (specification key: `recent`).

    Args:
        name (string): Memory name
            (<span style="color:#0000C0"><b>internal use</b></span>).
        capacity (int > 0): Memory capacity
            (<span style="color:#00C000"><b>default</b></span>: minimum capacity).
        values_spec (specification): Values specification
            (<span style="color:#0000C0"><b>internal use</b></span>).
        min_capacity (int >= 0): Minimum memory capacity
            (<span style="color:#0000C0"><b>internal use</b></span>).
        device (string): Device name
            (<span style="color:#00C000"><b>default</b></span>: inherit value of parent module).
        summary_labels ('all' | iter[string]): Labels of summaries to record
            (<span style="color:#00C000"><b>default</b></span>: inherit value of parent module).
    """

    def tf_retrieve_timesteps(self, n, past_horizon, future_horizon):
        one = tf.constant(value=1, dtype=util.tf_dtype(dtype='long'))
        capacity = tf.constant(value=self.capacity, dtype=util.tf_dtype(dtype='long'))

        # Check whether memory contains at least one valid timestep
        num_timesteps = tf.minimum(x=self.buffer_index, y=capacity) - past_horizon - future_horizon
        assertion = tf.debugging.assert_greater_equal(x=num_timesteps, y=one)

        # Most recent timestep indices range
        with tf.control_dependencies(control_inputs=(assertion,)):
            indices = tf.range(start=(self.buffer_index - n), limit=self.buffer_index)
            indices = tf.math.mod(x=(indices - future_horizon), y=capacity)

        return indices

    def tf_retrieve_episodes(self, n):
        zero = tf.constant(value=0, dtype=util.tf_dtype(dtype='long'))
        one = tf.constant(value=1, dtype=util.tf_dtype(dtype='long'))
        capacity = tf.constant(value=self.capacity, dtype=util.tf_dtype(dtype='long'))

        # Check whether memory contains at least one episode
        assertion = tf.debugging.assert_greater_equal(x=self.episode_count, y=one)

        # Get start and limit index for most recent n episodes
        with tf.control_dependencies(control_inputs=(assertion,)):
            start = self.terminal_indices[self.episode_count - n]
            limit = self.terminal_indices[self.episode_count]
            # Increment terminal of previous episode
            start = start + one
            limit = limit + one

            # Correct limit index if smaller than start index
            limit = limit + tf.where(condition=(limit < start), x=capacity, y=zero)

            # Most recent episode indices range
            indices = tf.range(start=start, limit=limit)
            indices = tf.math.mod(x=indices, y=capacity)

        return indices
