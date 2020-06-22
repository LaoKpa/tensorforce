# Copyright 2020 Tensorforce Team. All Rights Reserved.
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

from collections import OrderedDict

from tensorforce import TensorforceError
from tensorforce.agents import TensorforceAgent


class DoubleDQN(TensorforceAgent):
    """
    [Double DQN](https://arxiv.org/abs/1509.06461) agent (specification key: `double_dqn` or
    `ddqn`).

    Args:
        states (specification): States specification
            (<span style="color:#C00000"><b>required</b></span>, better implicitly specified via
            `environment` argument for `Agent.create(...)`), arbitrarily nested dictionary of state
            descriptions (usually taken from `Environment.states()`) with the following attributes:
            <ul>
            <li><b>type</b> (<i>"bool" | "int" | "float"</i>) &ndash; state data type
            (<span style="color:#00C000"><b>default</b></span>: "float").</li>
            <li><b>shape</b> (<i>int | iter[int]</i>) &ndash; state shape
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>num_values</b> (<i>int > 0</i>) &ndash; number of discrete state values
            (<span style="color:#C00000"><b>required</b></span> for type "int").</li>
            <li><b>min_value/max_value</b> (<i>float</i>) &ndash; minimum/maximum state value
            (<span style="color:#00C000"><b>optional</b></span> for type "float").</li>
            </ul>
        actions (specification): Actions specification
            (<span style="color:#C00000"><b>required</b></span>, better implicitly specified via
            `environment` argument for `Agent.create(...)`), arbitrarily nested dictionary of
            action descriptions (usually taken from `Environment.actions()`) with the following
            attributes:
            <ul>
            <li><b>type</b> (<i>"bool" | "int" | "float"</i>) &ndash; action data type
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>shape</b> (<i>int > 0 | iter[int > 0]</i>) &ndash; action shape
            (<span style="color:#00C000"><b>default</b></span>: scalar).</li>
            <li><b>num_values</b> (<i>int > 0</i>) &ndash; number of discrete action values
            (<span style="color:#C00000"><b>required</b></span> for type "int").</li>
            <li><b>min_value/max_value</b> (<i>float</i>) &ndash; minimum/maximum action value
            (<span style="color:#00C000"><b>optional</b></span> for type "float").</li>
            </ul>
        max_episode_timesteps (int > 0): Upper bound for numer of timesteps per episode
            (<span style="color:#00C000"><b>default</b></span>: not given, better implicitly
            specified via `environment` argument for `Agent.create(...)`).

        memory (int > 0): Replay memory capacity, has to fit at least maximum batch_size + maximum
            network/estimator horizon + 1 timesteps
            (<span style="color:#C00000"><b>required</b></span>).
        batch_size (parameter, int > 0): Number of timesteps per update batch
            (<span style="color:#C00000"><b>required</b></span>).

        network ("auto" | specification): Policy network configuration, see
            [networks](../modules/networks.html)
            (<span style="color:#00C000"><b>default</b></span>: "auto", automatically configured
            network).

        update_frequency ("never" | parameter, int > 0): Frequency of updates
            (<span style="color:#00C000"><b>default</b></span>: batch_size).
        start_updating (parameter, int >= batch_size): Number of timesteps before first update
            (<span style="color:#00C000"><b>default</b></span>: none).
        learning_rate (parameter, float > 0.0): Optimizer learning rate
            (<span style="color:#00C000"><b>default</b></span>: 3e-4).
        huber_loss (parameter, float > 0.0): Huber loss threshold
            (<span style="color:#00C000"><b>default</b></span>: no huber loss).

        horizon (parameter, int >= 1): n-step DQN, horizon of discounted-sum reward
            estimation before target network estimate
            (<span style="color:#00C000"><b>default</b></span>: 1).
        discount (parameter, 0.0 <= float <= 1.0): Discount factor for future rewards of
            discounted-sum reward estimation
            (<span style="color:#00C000"><b>default</b></span>: 0.99).
        predict_terminal_values (bool): Whether to predict the value of terminal states
            (<span style="color:#00C000"><b>default</b></span>: false).

        target_sync_frequency (parameter, int > 0): Interval between target network updates
            (<span style="color:#00C000"><b>default</b></span>: every update).
        target_update_weight (parameter, 0.0 < float <= 1.0): Target network update weight
            (<span style="color:#00C000"><b>default</b></span>: 1.0).

        l2_regularization (parameter, float >= 0.0): L2 regularization loss weight
            (<span style="color:#00C000"><b>default</b></span>: no L2 regularization).
        entropy_regularization (parameter, float >= 0.0): Entropy regularization loss weight, to
            discourage the policy distribution from being "too certain"
            (<span style="color:#00C000"><b>default</b></span>: no entropy regularization).

        preprocessing (dict[specification]): Preprocessing as layer or list of layers, see
            [preprocessing](../modules/preprocessing.html), specified per state-type or -name, and
            for reward/return/advantage
            (<span style="color:#00C000"><b>default</b></span>: none).
        exploration (parameter | dict[parameter], float >= 0.0): Exploration, defined as the
            probability for uniformly random output in case of `bool` and `int` actions, and the
            standard deviation of Gaussian noise added to every output in case of `float` actions,
            specified globally or per action-type or -name
            (<span style="color:#00C000"><b>default</b></span>: no exploration).
        variable_noise (parameter, float >= 0.0): Add Gaussian noise with given standard deviation
            to all trainable variables, as alternative exploration mechanism
            (<span style="color:#00C000"><b>default</b></span>: no variable noise).

        parallel_interactions (int > 0): Maximum number of parallel interactions to support,
            for instance, to enable multiple parallel episodes, environments or agents within an
            environment
            (<span style="color:#00C000"><b>default</b></span>: 1).
        config (specification): Additional configuration options:
            <ul>
            <li><b>name</b> (<i>string</i>) &ndash; Agent name, used e.g. for TensorFlow scopes and
            saver default filename
            (<span style="color:#00C000"><b>default</b></span>: "agent").
            <li><b>device</b> (<i>string</i>) &ndash; Device name
            (<span style="color:#00C000"><b>default</b></span>: TensorFlow default).
            <li><b>seed</b> (<i>int</i>) &ndash; Random seed to set for Python, NumPy (both set
            globally!) and TensorFlow, environment seed may have to be set separately for fully
            deterministic execution
            (<span style="color:#00C000"><b>default</b></span>: none).</li>
            <li><b>buffer_observe</b> (<i>false | "episode" | int > 0</i>) &ndash; Number of
            timesteps within an episode to buffer before calling the internal observe function, to
            reduce calls to TensorFlow for improved performance
            (<span style="color:#00C000"><b>default</b></span>: configuration-specific maximum
            number which can be buffered without affecting performance).</li>
            <li><b>always_apply_exploration</b> (<i>bool</i>) &ndash; Whether to always apply
            exploration, also for independent `act()` calls (final value in case of schedule)
            (<span style="color:#00C000"><b>default</b></span>: false).</li>
            <li><b>always_apply_variable_noise</b> (<i>bool</i>) &ndash; Whether to always apply
            variable noise, also for independent `act()` calls (final value in case of schedule)
            (<span style="color:#00C000"><b>default</b></span>: false).</li>
            <li><b>enable_int_action_masking</b> (<i>bool</i>) &ndash; Whether int action options
            can be masked via an optional "[ACTION-NAME]_mask" state input
            (<span style="color:#00C000"><b>default</b></span>: true).</li>
            <li><b>create_tf_assertions</b> (<i>bool</i>) &ndash; Whether to create internal
            TensorFlow assertion operations
            (<span style="color:#00C000"><b>default</b></span>: true).</li>
            </ul>
        saver (specification): TensorFlow checkpoint manager configuration for periodic implicit
            saving, as alternative to explicit saving via agent.save(), with the following
            attributes (<span style="color:#00C000"><b>default</b></span>: no saver):
            <ul>
            <li><b>directory</b> (<i>path</i>) &ndash; saver directory
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>filename</b> (<i>string</i>) &ndash; model filename
            (<span style="color:#00C000"><b>default</b></span>: agent name).</li>
            <li><b>frequency</b> (<i>int > 0</i>) &ndash; how frequently to save the model
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>unit</b> (<i>"timesteps" | "episodes" | "updates"</i>) &ndash; frequency unit
            (<span style="color:#00C000"><b>default</b></span>: updates).</li>
            <li><b>max-checkpoints</b> (<i>int > 0</i>) &ndash; maximum number of checkpoints to
            keep (<span style="color:#00C000"><b>default</b></span>: 5).</li>
            <li><b>max-hour-frequency</b> (<i>int > 0</i>) &ndash; ignoring max-checkpoints,
            definitely keep a checkpoint in given hour frequency
            (<span style="color:#00C000"><b>default</b></span>: none).</li>
            </ul>
        summarizer (specification): TensorBoard summarizer configuration with the following
            attributes (<span style="color:#00C000"><b>default</b></span>: no summarizer):
            <ul>
            <li><b>directory</b> (<i>path</i>) &ndash; summarizer directory
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>flush</b> (<i>int > 0</i>) &ndash; how frequently in seconds to flush the
            summary writer (<span style="color:#00C000"><b>default</b></span>: 10).</li>
            <li><b>max-summaries</b> (<i>int > 0</i>) &ndash; maximum number of summaries to keep
            (<span style="color:#00C000"><b>default</b></span>: 5).</li>
            <li><b>labels</b> (<i>"all" | iter[string]</i>) &ndash; which summaries to record
            (<span style="color:#00C000"><b>default</b></span>: only "graph"):</li>
            <li>"distribution": distribution parameters like probabilities or mean and stddev
            (timestep-based, interpretation not obvious in case of value-based algorithms)</li>
            <li>"entropy": entropy of (per-action) policy distribution(s) (timestep-based,
            interpretation not obvious in case of value-based algorithms)</li>
            <li>"graph": computation graph</li>
            <li>"kl-divergence": KL-divergence of previous and updated (per-action) policy
            distribution(s) (update-based, interpretation not obvious in case of value-based
            algorithms)</li>
            <li>"loss": policy and baseline loss plus loss components (update-based)</li>
            <li>"parameters": parameter values (according to parameter unit)</li>
            <li>"reward": timestep and episode reward, plus intermediate reward/return estimates
            (timestep/episode/update-based)</li>
            <li>"update-norm": global norm of update (update-based)</li>
            <li>"updates": mean and variance of update tensors per variable (update-based)</li>
            <li>"variables": mean of trainable variables tensors (update-based)</li>
            </ul>
        recorder (specification): Experience traces recorder configuration, currently not including
            internal states, with the following attributes
            (<span style="color:#00C000"><b>default</b></span>: no recorder):
            <ul>
            <li><b>directory</b> (<i>path</i>) &ndash; recorder directory
            (<span style="color:#C00000"><b>required</b></span>).</li>
            <li><b>frequency</b> (<i>int > 0</i>) &ndash; how frequently in episodes to record
            traces (<span style="color:#00C000"><b>default</b></span>: every episode).</li>
            <li><b>start</b> (<i>int >= 0</i>) &ndash; how many episodes to skip before starting to
            record traces (<span style="color:#00C000"><b>default</b></span>: 0).</li>
            <li><b>max-traces</b> (<i>int > 0</i>) &ndash; maximum number of traces to keep
            (<span style="color:#00C000"><b>default</b></span>: all).</li>
    """

    def __init__(
        # Required
        self, states, actions, memory, batch_size,
        # Environment
        max_episode_timesteps=None,
        # Network
        network='auto',
        # Optimization
        update_frequency=None, start_updating=None, learning_rate=3e-4, huber_loss=0.0,
        # Reward estimation
        horizon=1, discount=0.99, predict_terminal_values=False,
        # Target network
        target_sync_frequency=1, target_update_weight=1.0,
        # Preprocessing
        preprocessing=None,
        # Exploration
        exploration=0.0, variable_noise=0.0,
        # Regularization
        l2_regularization=0.0, entropy_regularization=0.0,
        # Parallel interactions
        parallel_interactions=1,
        # Config, saver, summarizer, recorder
        config=None, saver=None, summarizer=None, recorder=None,
        # Deprecated
        estimate_terminal=None, **kwargs
    ):
        if estimate_terminal is not None:
            raise TensorforceError.deprecated(
                name='DoubleDQN', argument='estimate_terminal',
                replacement='predict_terminal_values'
            )

        self.spec = OrderedDict(
            agent='dqn',
            states=states, actions=actions, memory=memory, batch_size=batch_size,
            max_episode_timesteps=max_episode_timesteps,
            network=network,
            update_frequency=update_frequency, start_updating=start_updating,
            learning_rate=learning_rate, huber_loss=huber_loss,
            horizon=horizon, discount=discount, predict_terminal_values=predict_terminal_values,
            target_sync_frequency=target_sync_frequency, target_update_weight=target_update_weight,
            preprocessing=preprocessing,
            exploration=exploration, variable_noise=variable_noise,
            l2_regularization=l2_regularization, entropy_regularization=entropy_regularization,
            parallel_interactions=parallel_interactions,
            config=config, saver=saver, summarizer=summarizer, recorder=recorder
        )

        policy = dict(network=network, temperature=0.0)

        memory = dict(type='replay', capacity=memory)

        update = dict(unit='timesteps', batch_size=batch_size)
        if update_frequency is not None:
            update['frequency'] = update_frequency
        if start_updating is not None:
            update['start'] = start_updating

        optimizer = dict(type='adam', learning_rate=learning_rate)
        objective = dict(type='value', value='action', huber_loss=huber_loss)

        reward_estimation = dict(
            horizon=horizon, discount=discount, predict_horizon_values='late',
            estimate_advantage=False, predict_action_values=True,
            predict_terminal_values=predict_terminal_values
        )

        baseline_policy = policy
        baseline_optimizer = dict(
            type='synchronization', sync_frequency=target_sync_frequency,
            update_weight=target_update_weight
        )
        baseline_objective = None

        super().__init__(
            # Agent
            states=states, actions=actions, max_episode_timesteps=max_episode_timesteps,
            parallel_interactions=parallel_interactions, config=config, recorder=recorder,
            # Model
            preprocessing=preprocessing, exploration=exploration, variable_noise=variable_noise,
            l2_regularization=l2_regularization, saver=saver, summarizer=summarizer,
            # TensorforceModel
            policy=policy, memory=memory, update=update, optimizer=optimizer, objective=objective,
            reward_estimation=reward_estimation, baseline_policy=baseline_policy,
            baseline_optimizer=baseline_optimizer, baseline_objective=baseline_objective,
            entropy_regularization=entropy_regularization, **kwargs
        )