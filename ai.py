from tensorflow.keras.models import Model
from tensorflow.keras.layers import *
import tensorflow.keras as keras
import tensorflow as tf
import snake
from snake import Game
import gym
import numpy as np
from gym import spaces
import os


def map_int_to_direction(i):
    if i == 0:
        return snake.UP
    elif i == 1:
        return snake.DOWN
    elif i == 2:
        return snake.LEFT
    elif i == 3:
        return snake.RIGHT


class SnakeEnvironment(gym.Env):
    def __init__(self):
        super(SnakeEnvironment, self)
        self.game = Game()
        self.action_space = spaces.Discrete(4)  # Up, Down, Left, Right
        self.observation_space = spaces.Box(low=-1, high=3, shape=(snake.BOARD_SIZE ** 2 + 4,), dtype=np.float32)

        # Number of turns since the last food was found
        self.last_food_found = 0

    def reset(self):
        self.game.reset()
        self.last_food_found = 0
        return self.next_observation()

    def next_observation(self):
        x = np.array(self.game.get_board()).reshape(snake.BOARD_SIZE ** 2)
        head = self.game.snake.get_head_position()
        xdiff = head.x - self.game.food.position.x
        ydiff = head.y - self.game.food.position.y
        x = np.append(x, [xdiff, ydiff, head.x, head.y])
        return x

    def take_action(self, action):
        self.game.snake.turn(map_int_to_direction(action))
        self.game.tick()
        self.game.handle_inputs()

    def render(self):
        self.game.render()

    def get_reward(self):
        reward = 0
        if self.game.snake.died:
            reward -= 0.5
            self.game.snake.died = False
        if self.game.snake.found_food:
            self.last_food_found = 0
            reward += 1
            self.game.snake.found_food = False
        if self.last_food_found > (snake.BOARD_SIZE ** 2):
            reward -= 1
            self.last_food_found = 0
        # reward = max(-1, min(1, reward))  # Clamp to [-1, 1]
        return reward

    def step(self, action):
        self.last_food_found += 1
        self.take_action(action)
        done = self.game.snake.died
        reward = self.get_reward()
        obs = self.next_observation()
        return obs, reward, done, {}

    def seed(self, s):
        self.game.food.seed(s)


def train(load_model='none'):
    # Most of the code in this function is from the Keras docs
    # Specifically, https://keras.io/examples/rl/actor_critic_cartpole/
    # The CartPole environment has been replaced with an extension of an OpenAI Gym Environment class for use with
    # the actor critic method

    # Directory to save and load the model from
    dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(dir, 'data', 'snake-model')

    seed = 100
    gamma = 0.99  # Discount factor for past rewards
    max_steps_per_episode = 1000
    env = SnakeEnvironment()  # Create the environment
    env.seed(seed)
    eps = np.finfo(np.float32).eps.item()  # Smallest number such that 1.0 + eps != 1.0
    optimizer = keras.optimizers.Adam(learning_rate=0.01)
    huber_loss = keras.losses.Huber()

    num_inputs = snake.BOARD_SIZE ** 2 + 4
    num_actions = 4

    inputs = Input(batch_input_shape=(1, num_inputs), name='input')
    common = Dense(num_inputs, activation='relu', name='common')(inputs)
    action = Dense(4, activation='softmax', name='output')(common)
    critic = Dense(1, name='critic')(common)

    model = Model(inputs=inputs, outputs=[action, critic])
    if load_model == 'best':
        model.load_weights(filename+'-best')
    elif load_model == 'last':
        model.load_weights(filename+'-last')

    action_probs_history = []
    critic_value_history = []
    rewards_history = []
    running_reward = 0
    episode_count = 0

    best_reward = -1000

    while True:  # Run until solved
        state = env.reset()
        env.seed(seed)
        episode_reward = 0
        with tf.GradientTape() as tape:
            for timestep in range(1, max_steps_per_episode):
                env.render()  # Adding this line would show the attempts of the agent in a pop up window.

                state = tf.convert_to_tensor(state)
                state = tf.expand_dims(state, 0)

                # Predict action probabilities and estimated future rewards
                # from environment state
                action_probs, critic_value = model(state)
                critic_value_history.append(critic_value[0, 0])

                # Sample action from action probability distribution
                action = np.random.choice(num_actions, p=np.squeeze(action_probs))
                action_probs_history.append(tf.math.log(action_probs[0, action]))

                # Apply the sampled action in our environment
                state, reward, done, _ = env.step(action)
                rewards_history.append(reward)
                episode_reward += reward

                if done:
                    break

            # Update running reward to check condition for solving
            running_reward = 0.05 * episode_reward + (1 - 0.05) * running_reward

            # Calculate expected value from rewards
            # - At each timestep what was the total reward received after that timestep
            # - Rewards in the past are discounted by multiplying them with gamma
            # - These are the labels for our critic
            returns = []
            discounted_sum = 0
            for r in rewards_history[::-1]:
                discounted_sum = r + gamma * discounted_sum
                returns.insert(0, discounted_sum)

            # Normalize
            returns = np.array(returns)
            returns = (returns - np.mean(returns)) / (np.std(returns) + eps)
            returns = returns.tolist()

            # Calculating loss values to update our network
            history = zip(action_probs_history, critic_value_history, returns)
            actor_losses = []
            critic_losses = []
            for log_prob, value, ret in history:
                # At this point in history, the critic estimated that we would get a
                # total reward = `value` in the future. We took an action with log probability
                # of `log_prob` and ended up recieving a total reward = `ret`.
                # The actor must be updated so that it predicts an action that leads to
                # high rewards (compared to critic's estimate) with high probability.
                diff = ret - value
                actor_losses.append(-log_prob * diff)  # actor loss

                # The critic must be updated so that it predicts a better estimate of
                # the future rewards.
                critic_losses.append(
                    huber_loss(tf.expand_dims(value, 0), tf.expand_dims(ret, 0))
                )

            # Backpropagation
            loss_value = sum(actor_losses) + sum(critic_losses)
            grads = tape.gradient(loss_value, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

            # Clear the loss and reward history
            action_probs_history.clear()
            critic_value_history.clear()
            rewards_history.clear()

        # Log details
        episode_count += 1
        if episode_reward > best_reward:
            best_reward = episode_reward
            model.save_weights(filename+'-best', overwrite=True)
        model.save_weights(filename+'-last', overwrite=True)

        if episode_count % 10 == 0:
            template = "running reward: {:.2f} at episode {}"
            print(template.format(running_reward, episode_count))

        if running_reward > 50:  # Condition to consider the task solved
            print("Solved at episode {}!".format(episode_count))
            break


def main():
    print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
    train(load_model='last')


if __name__ == "__main__":
    main()
