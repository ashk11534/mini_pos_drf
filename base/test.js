const list = [10, 20, 30, 40, 50];

class Person {
  constructor(name, age) {
    this.name = name;
    this.age = age;
  }

  details() {
    console.log(`Hello ${this.name}. Your age is: ${this.age}`);
  }
}

const p1 = new Person("Ashik", 28);

const sum = list.reduce(
  (accumulator, currentItem) => accumulator + currentItem,
  0,
);

console.log(sum);

const root = document.createElement("div");

const heading = document.createElement("h1");
heading.innerHTML = "Hello World";

root.appendChild(heading);
