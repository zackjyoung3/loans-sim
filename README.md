# loans-sim

## Purpose
- This will be a relatively simple impl. All that I want to do is have a mechanism by which I can observe different asset/liability long-term accumulation based on a decision at a point in time to either divert funds to paying off loans or to investing in market/putting funds in a high yields savings account

## Requirements
- Support 4 basic point in time decisions
  - Just let cash sit (base case) 
  - Pay off loan w surplus captial (assuming fixed rate)
  - Put cash in high yield savings account paying x% (assuming fixed rate)
  - Put cash in S & P 500 (for simplicity to start, ideally make generic enough that the user can enter in any arbitrary ticker and you will make projections)
- Obviously, letting cash sit, paying off loan w surplus capital and putting cash in a high yield savings account will always yeild the same performance regardless of time period (due to our assumption that rate/yield is fixed for loans/yield respectively)
- Thinking that I am going to want to let the user specify a time in which they want to see this sim take place from to make the market sim interesting
- Maybe even present a mechanism by which the user can put in some arbitrary time frame which they can test over so we can accum expected market returns rather than having faulty point in time reference which obviously could potentially be a poor representation of what a loan payer should expect when considering how they should allocate their funds   
- Start with sim just presenting final findings in accumulated net differential at the end of specified accumulation time fram
  - Perhaps in time move to a more sophisticated approach that will show chart of all expected deltas over many years  
