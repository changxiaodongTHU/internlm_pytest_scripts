# Runner

## process

1. read config, get the map from `task_type` to `config parser`
2. read task config, parse config using the specific parser, get `cases` and `env setup`
3. instantiate `Runner`, run all cases in one way(depends on config)

## feature

1. Runner will guarantee that the task will be completed
2. we should get the test progress easily
3. we can stop test anytime
4. we can resume a test(that's important)
5. we will collect start time tik and count time tik of each test case

## design

### start

### stop

### resume

### replay

### batch run code

## other part

### get_progress(batch of runner)

### gather results
